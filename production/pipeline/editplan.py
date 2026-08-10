"""The edit plan: the structured contract between creative decisions and rendering.

Stages exchange this object rather than prose. The renderer reads only the plan;
the quality controller checks the render against the same plan.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class TextCue:
    """One on-screen text element."""

    id: str
    text: str
    role: str                      # hook | reveal | cta | label | secondary
    style: str
    start_seconds: float
    end_seconds: float
    y: int
    align: str = "center"
    animation: str = "fade"
    box: dict[str, int] | None = None      # estimated pixel bounds, for safe-zone checks
    rationale: str = ""

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Placement:
    """Where a video source sits on the 1080x1920 canvas."""

    x: int
    y: int
    width: int
    height: int

    @property
    def area_fraction(self) -> float:
        return (self.width * self.height) / (1080 * 1920)

    def as_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["area_fraction"] = round(self.area_fraction, 4)
        return data


@dataclass
class SecondaryClip:
    """A supporting clip and the window in which it is visible."""

    path: str
    label: str
    role: str
    mode: str                       # cutaway | inset | band
    placement: Placement | None
    start_seconds: float
    end_seconds: float
    source_in: float = 0.0
    loop: bool = False
    rationale: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "label": self.label,
            "role": self.role,
            "mode": self.mode,
            "placement": self.placement.as_dict() if self.placement else None,
            "start_seconds": round(self.start_seconds, 3),
            "end_seconds": round(self.end_seconds, 3),
            "source_in": round(self.source_in, 3),
            "loop": self.loop,
            "rationale": self.rationale,
        }


@dataclass
class Emphasis:
    """Zoom pulse marking the transition."""

    enabled: bool
    at_seconds: float
    amount: float
    attack_seconds: float
    release_seconds: float

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AudioPlan:
    """What happens to the mix audio. Creative content is never altered."""

    source_path: str
    normalise: bool
    target_lufs: float
    true_peak_db: float
    measured_lufs: float | None
    reason: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ExperimentPlan:
    """Optional hypothesis attached to this render."""

    hypothesis: str
    variable: str
    control_reference: str
    expected_effect: str
    status: str = "awaiting_results"

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class EditPlan:
    """Complete, executable description of one render."""

    job_id: str
    revision: int
    format_family: str
    template_name: str

    # Spotify source window and resulting output timing.
    source_in_seconds: float
    source_out_seconds: float
    duration_seconds: float
    transition_output_seconds: float
    transition_window: tuple[float, float]

    layout_mode: str
    spotify_placement: Placement
    background: str                        # solid colour or "blurred_spotify"
    # How far the capture is cropped towards its song labels and waveform,
    # enlarging them on screen. 0 keeps the whole frame.
    spotify_content_zoom: float = 0.0
    # Fraction of frame width deliberately cut from each side of the waveform to
    # let the zoom go past its natural ceiling. Opt-in only.
    waveform_end_trim: float = 0.0
    secondary_clips: list[SecondaryClip] = field(default_factory=list)
    text_cues: list[TextCue] = field(default_factory=list)
    emphasis: Emphasis | None = None
    progress_bar: dict[str, Any] | None = None
    audio: AudioPlan | None = None

    hook_text: str = ""
    cta_text: str = ""
    retention_hypothesis: str = ""
    creative_rationale: list[str] = field(default_factory=list)
    decisions: list[dict[str, str]] = field(default_factory=list)
    experiment: ExperimentPlan | None = None
    research_refs: list[str] = field(default_factory=list)
    preference_refs: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    # True when auto-select collapsed into a zero-asset format because higher-value
    # families lacked clips or metadata — not when the job forced that format.
    empty_asset_fallback: bool = False

    def add_decision(self, decision: str, rationale: str, stage: str = "creative") -> None:
        self.decisions.append({"decision": decision, "rationale": rationale, "stage": stage})

    def as_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "revision": self.revision,
            "format_family": self.format_family,
            "template_name": self.template_name,
            "source_in_seconds": round(self.source_in_seconds, 3),
            "source_out_seconds": round(self.source_out_seconds, 3),
            "duration_seconds": round(self.duration_seconds, 3),
            "transition_output_seconds": round(self.transition_output_seconds, 3),
            "transition_window": [
                round(self.transition_window[0], 3), round(self.transition_window[1], 3),
            ],
            "layout_mode": self.layout_mode,
            "spotify_placement": self.spotify_placement.as_dict(),
            "background": self.background,
            "spotify_content_zoom": round(self.spotify_content_zoom, 4),
            "waveform_end_trim": round(self.waveform_end_trim, 4),
            "secondary_clips": [clip.as_dict() for clip in self.secondary_clips],
            "text_cues": [cue.as_dict() for cue in self.text_cues],
            "emphasis": self.emphasis.as_dict() if self.emphasis else None,
            "progress_bar": self.progress_bar,
            "audio": self.audio.as_dict() if self.audio else None,
            "hook_text": self.hook_text,
            "cta_text": self.cta_text,
            "retention_hypothesis": self.retention_hypothesis,
            "creative_rationale": self.creative_rationale,
            "decisions": self.decisions,
            "experiment": self.experiment.as_dict() if self.experiment else None,
            "research_refs": self.research_refs,
            "preference_refs": self.preference_refs,
            "warnings": self.warnings,
            "empty_asset_fallback": self.empty_asset_fallback,
        }

    def segments_for_rule_check(self) -> list[dict[str, Any]]:
        """Cut boundaries expressed against the source timeline."""
        return [{
            "id": "spotify_main",
            "source_in": self.source_in_seconds,
            "source_out": self.source_out_seconds,
            "speed": 1.0,
        }]
