"""Audio analysis: transition detection, beat estimation and loudness.

The transition is the video's payoff, so locating it accurately drives trimming,
visual emphasis and text timing. Detection is a spectral-flux novelty search over
the decoded mono signal — deterministic, local, and dependent only on numpy.

Every returned measurement carries a confidence label so downstream stages can
say how the number was obtained rather than presenting an estimate as fact.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .probe import MediaError, decode_mono_pcm, measure_loudness

SAMPLE_RATE = 22050
FFT_SIZE = 2048


@dataclass
class TransitionEstimate:
    """Where the mix transition happens and how the number was obtained."""

    seconds: float
    start_seconds: float
    end_seconds: float
    method: str
    confidence: str
    novelty_score: float = 0.0
    alternatives: list[float] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "seconds": round(self.seconds, 3),
            "start_seconds": round(self.start_seconds, 3),
            "end_seconds": round(self.end_seconds, 3),
            "method": self.method,
            "confidence": self.confidence,
            "novelty_score": round(self.novelty_score, 4),
            "alternatives": [round(value, 3) for value in self.alternatives],
            "notes": self.notes,
        }


@dataclass
class BeatGrid:
    """Estimated tempo and beat positions."""

    bpm: float
    beat_times: list[float]
    confidence: str
    method: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "bpm": round(self.bpm, 2),
            "beat_count": len(self.beat_times),
            "beat_times": [round(value, 3) for value in self.beat_times[:512]],
            "confidence": self.confidence,
            "method": self.method,
        }

    def nearest_beat(self, timestamp: float) -> float:
        if not self.beat_times:
            return timestamp
        return min(self.beat_times, key=lambda beat: abs(beat - timestamp))


def _onset_envelope(samples, hop: int):
    """Spectral-flux onset envelope: positive frame-to-frame magnitude change."""
    import numpy as np

    if samples.size < FFT_SIZE * 2:
        raise MediaError("audio too short to analyse")

    window = np.hanning(FFT_SIZE).astype("float32")
    frame_count = 1 + (samples.size - FFT_SIZE) // hop
    frame_count = max(frame_count, 1)

    indices = np.arange(FFT_SIZE)[None, :] + hop * np.arange(frame_count)[:, None]
    frames = samples[indices] * window
    spectra = np.abs(np.fft.rfft(frames, axis=1))

    # Log compression keeps loud sections from dominating the novelty curve.
    spectra = np.log1p(spectra * 8.0)
    flux = np.diff(spectra, axis=0)
    envelope = np.maximum(flux, 0.0).sum(axis=1)
    return np.concatenate([[0.0], envelope]).astype("float32"), spectra


def _smooth(values, width: int):
    import numpy as np

    if width <= 1:
        return values
    kernel = np.ones(width, dtype="float32") / float(width)
    return np.convolve(values, kernel, mode="same")


def detect_transition(
    media_path: Path | str,
    *,
    hop_seconds: float = 0.10,
    search_start_fraction: float = 0.10,
    search_end_fraction: float = 0.92,
    declared_seconds: float | None = None,
    duration_seconds: float | None = None,
) -> TransitionEstimate:
    """Locate the mix transition.

    A creator-declared timestamp always wins — the pipeline never overrides a
    stated fact with an estimate. Otherwise the strongest timbre change inside the
    search window is used.
    """
    if declared_seconds is not None:
        declared = float(declared_seconds)
        return TransitionEstimate(
            seconds=declared,
            start_seconds=max(0.0, declared - 1.2),
            end_seconds=declared + 2.0,
            method="declared_in_job",
            confidence="high",
            notes=["timestamp supplied in job.yaml; no detection performed"],
        )

    import numpy as np

    hop = max(int(SAMPLE_RATE * hop_seconds), 256)
    samples = decode_mono_pcm(media_path, sample_rate=SAMPLE_RATE)
    total_seconds = duration_seconds or (samples.size / SAMPLE_RATE)

    envelope, spectra = _onset_envelope(samples, hop)
    times = np.arange(envelope.size) * (hop / SAMPLE_RATE)

    # A timbre change is a sustained shift in the spectral profile, not a single
    # onset. Compare the averaged spectrum before and after each candidate frame.
    window_frames = max(int(2.0 / (hop / SAMPLE_RATE)), 4)
    if spectra.shape[0] < window_frames * 2 + 2:
        raise MediaError("audio too short for transition analysis")

    cumulative = np.cumsum(spectra, axis=0)

    def window_mean(start: int, end: int):
        start = max(start, 0)
        end = min(end, spectra.shape[0] - 1)
        if end <= start:
            return spectra[start]
        return (cumulative[end] - cumulative[start]) / float(end - start)

    lower = int(total_seconds * search_start_fraction / (hop / SAMPLE_RATE))
    upper = int(total_seconds * search_end_fraction / (hop / SAMPLE_RATE))
    lower = max(lower, window_frames)
    upper = min(upper, spectra.shape[0] - window_frames - 1)

    notes: list[str] = []
    if upper <= lower:
        midpoint = total_seconds / 2.0
        return TransitionEstimate(
            seconds=midpoint,
            start_seconds=max(0.0, midpoint - 1.2),
            end_seconds=min(total_seconds, midpoint + 2.0),
            method="fallback_midpoint",
            confidence="low",
            notes=["recording too short for a meaningful search window"],
        )

    candidates = np.arange(lower, upper)
    novelty = np.zeros(candidates.size, dtype="float32")
    for position, frame in enumerate(candidates):
        before = window_mean(frame - window_frames, frame)
        after = window_mean(frame, frame + window_frames)
        denominator = np.linalg.norm(before) * np.linalg.norm(after)
        if denominator <= 1e-9:
            continue
        # Cosine distance between spectral profiles: 0 = identical timbre.
        novelty[position] = 1.0 - float(np.dot(before, after) / denominator)

    novelty = _smooth(novelty, 3)
    if float(novelty.max()) <= 1e-6:
        midpoint = total_seconds / 2.0
        return TransitionEstimate(
            seconds=midpoint,
            start_seconds=max(0.0, midpoint - 1.2),
            end_seconds=min(total_seconds, midpoint + 2.0),
            method="fallback_midpoint",
            confidence="low",
            notes=["no timbre change detected; the recording may be a single track"],
        )

    best_index = int(np.argmax(novelty))
    best_frame = int(candidates[best_index])
    best_time = float(times[min(best_frame, times.size - 1)])
    peak = float(novelty[best_index])

    # Runner-up peaks at least 1.5s away, for the report.
    alternatives: list[float] = []
    ordering = np.argsort(novelty)[::-1]
    for index in ordering[1:40]:
        candidate_time = float(times[min(int(candidates[index]), times.size - 1)])
        if all(abs(candidate_time - existing) > 1.5 for existing in [best_time, *alternatives]):
            alternatives.append(candidate_time)
        if len(alternatives) >= 3:
            break

    mean = float(novelty.mean())
    spread = float(novelty.std()) or 1e-6
    prominence = (peak - mean) / spread
    if prominence >= 3.0:
        confidence = "high"
    elif prominence >= 1.8:
        confidence = "medium"
    else:
        confidence = "low"
        notes.append(
            "the strongest timbre change is not clearly separated from the rest of the "
            "recording; declare transition.seconds in job.yaml to be certain"
        )

    return TransitionEstimate(
        seconds=best_time,
        start_seconds=max(0.0, best_time - 1.2),
        end_seconds=min(total_seconds, best_time + 2.0),
        method="spectral_flux_novelty",
        confidence=confidence,
        novelty_score=peak,
        alternatives=alternatives,
        notes=notes,
    )


def estimate_beats(
    media_path: Path | str,
    *,
    hop_seconds: float = 0.01161,
    bpm_range: tuple[float, float] = (70.0, 175.0),
    max_seconds: float = 60.0,
) -> BeatGrid | None:
    """Estimate tempo and beat positions by autocorrelating the onset envelope.

    Returns None when the signal gives no usable periodicity; callers must treat a
    missing beat grid as "align to the transition only".
    """
    import numpy as np

    try:
        samples = decode_mono_pcm(media_path, sample_rate=SAMPLE_RATE)
    except MediaError:
        return None
    if samples.size == 0:
        return None
    samples = samples[: int(SAMPLE_RATE * max_seconds)]

    hop = max(int(SAMPLE_RATE * hop_seconds), 128)
    try:
        envelope, _ = _onset_envelope(samples, hop)
    except MediaError:
        return None
    if envelope.size < 64:
        return None

    envelope = envelope - envelope.mean()
    frame_rate = SAMPLE_RATE / hop

    correlation = np.correlate(envelope, envelope, mode="full")[envelope.size - 1:]
    if correlation.size < 8 or correlation[0] <= 0:
        return None
    correlation = correlation / correlation[0]

    min_lag = max(int(frame_rate * 60.0 / bpm_range[1]), 1)
    max_lag = min(int(frame_rate * 60.0 / bpm_range[0]), correlation.size - 1)
    if max_lag <= min_lag:
        return None

    window = correlation[min_lag:max_lag]
    best_lag = int(np.argmax(window)) + min_lag
    strength = float(correlation[best_lag])
    if strength < 0.08:
        return None

    period_seconds = best_lag / frame_rate
    bpm = 60.0 / period_seconds if period_seconds > 0 else 0.0
    if not bpm_range[0] <= bpm <= bpm_range[1]:
        return None

    # Phase: the offset within the first period carrying the most onset energy.
    period_frames = best_lag
    folded = np.zeros(period_frames, dtype="float32")
    for offset in range(period_frames):
        folded[offset] = envelope[offset::period_frames].sum()
    phase_frames = int(np.argmax(folded))
    phase_seconds = phase_frames / frame_rate

    total_seconds = samples.size / SAMPLE_RATE
    beat_times: list[float] = []
    position = phase_seconds
    while position < total_seconds:
        beat_times.append(round(position, 4))
        position += period_seconds

    if strength >= 0.30:
        confidence = "medium"
    else:
        confidence = "low"

    return BeatGrid(
        bpm=bpm,
        beat_times=beat_times,
        confidence=confidence,
        method="onset_autocorrelation",
    )


@dataclass
class LoudnessReport:
    integrated_lufs: float
    true_peak_db: float
    loudness_range: float
    needs_normalisation: bool
    reason: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "integrated_lufs": round(self.integrated_lufs, 2),
            "true_peak_db": round(self.true_peak_db, 2),
            "loudness_range": round(self.loudness_range, 2),
            "needs_normalisation": self.needs_normalisation,
            "reason": self.reason,
        }


def analyse_loudness(
    media_path: Path | str,
    *,
    target_lufs: float = -14.0,
    tolerance: float = 1.0,
    true_peak_ceiling: float = -1.5,
) -> LoudnessReport | None:
    """Measure loudness and decide whether normalisation is warranted.

    Normalisation is a technical correction, not a creative change: it runs only
    when the source is measurably outside the target window or is clipping.
    """
    try:
        measured = measure_loudness(media_path)
    except MediaError:
        return None

    integrated = measured["input_i"]
    true_peak = measured["input_tp"]
    deviation = abs(integrated - target_lufs)

    if true_peak > true_peak_ceiling:
        return LoudnessReport(
            integrated, true_peak, measured["input_lra"], True,
            f"true peak {true_peak:.2f} dBTP exceeds the {true_peak_ceiling} dBTP ceiling",
        )
    if deviation > tolerance:
        return LoudnessReport(
            integrated, true_peak, measured["input_lra"], True,
            f"integrated loudness {integrated:.2f} LUFS is {deviation:.2f} dB from "
            f"the {target_lufs} LUFS target",
        )
    return LoudnessReport(
        integrated, true_peak, measured["input_lra"], False,
        f"already within {tolerance} dB of {target_lufs} LUFS; left untouched",
    )
