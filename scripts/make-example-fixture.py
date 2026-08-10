#!/usr/bin/env python3
"""Generate a synthetic Spotify-mix screen recording for testing the pipeline.

Real captures are never committed (SECURITY.md), so the repository ships a
generator instead. The fixture imitates the parts of the Spotify now-playing
screen the pipeline actually reads: a large artwork block, a song label that
changes at the transition, and a live waveform rendered from the audio.

The audio contains two tonally distinct "tracks" joined by a real crossfade, so
transition detection has something genuine to find.

    python3 scripts/make-example-fixture.py --out examples/inputs/demo-mix
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
]

CANVAS_WIDTH = 1080
CANVAS_HEIGHT = 1920


def find_font() -> str:
    for candidate in FONT_CANDIDATES:
        if Path(candidate).is_file():
            return candidate
    raise SystemExit("No usable font found; install fonts-dejavu-core.")


def run(cmd: list[str]) -> None:
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        tail = "\n  ".join((proc.stderr or "").strip().splitlines()[-12:])
        raise SystemExit(f"ffmpeg failed:\n  {' '.join(cmd[:8])} …\n  {tail}")


def build_audio(
    destination: Path, first_seconds: float, second_seconds: float, blend_seconds: float
) -> float:
    """Two tonally distinct tracks joined by a real crossfade."""
    # Track one: low, warm, 100 BPM pulse.
    track_one = (
        "sine=frequency=110:duration={d},"
        "aeval=val(0)*(0.55+0.45*sin(2*PI*1.667*t)):c=same".format(d=first_seconds + blend_seconds)
    )
    # Track two: brighter harmonic content, faster pulse — a clear timbre change.
    track_two = (
        "sine=frequency=330:duration={d},"
        "aeval=val(0)*(0.5+0.5*sin(2*PI*2.167*t)):c=same".format(d=second_seconds + blend_seconds)
    )

    run([
        "ffmpeg", "-y", "-v", "error",
        "-f", "lavfi", "-i", track_one,
        "-f", "lavfi", "-i", f"sine=frequency=220:duration={first_seconds + blend_seconds}",
        "-f", "lavfi", "-i", track_two,
        "-f", "lavfi", "-i", f"sine=frequency=660:duration={second_seconds + blend_seconds}",
        "-filter_complex",
        "[0:a][1:a]amix=inputs=2:weights=1 0.5,volume=0.9[a1];"
        "[2:a][3:a]amix=inputs=2:weights=1 0.7,volume=0.9[a2];"
        f"[a1][a2]acrossfade=d={blend_seconds}:c1=tri:c2=tri,"
        "loudnorm=I=-16:TP=-1.5:LRA=11[out]",
        "-map", "[out]", "-ac", "2", "-ar", "48000", str(destination),
    ])
    return first_seconds + second_seconds + blend_seconds


def build_recording(
    audio_path: Path,
    destination: Path,
    *,
    duration: float,
    transition_at: float,
    first_title: str,
    first_artist: str,
    second_title: str,
    second_artist: str,
) -> None:
    font = find_font()

    # Layout mirrors production/config/crop-profiles.yaml `vertical_full`.
    art_x, art_y, art_size = 120, 280, 840
    title_y = 1215
    artist_y = 1300
    wave_y = 1390
    wave_height = 220
    progress_y = 1660

    def text(value: str, y: int, size: int, colour: str, start: float, end: float) -> str:
        escaped = value.replace(":", r"\:").replace("'", r"\'")
        return (
            f"drawtext=fontfile='{font}':text='{escaped}':fontsize={size}:"
            f"fontcolor={colour}:x=(w-text_w)/2:y={y}:"
            f"enable='between(t,{start:.3f},{end:.3f})'"
        )

    background = ",".join([
        # Artwork block, recoloured when the second track takes over.
        f"drawbox=x={art_x}:y={art_y}:w={art_size}:h={art_size}:color=0x1E5F3A@1:t=fill:"
        f"enable='lt(t,{transition_at:.3f})'",
        f"drawbox=x={art_x}:y={art_y}:w={art_size}:h={art_size}:color=0x6A2E7A@1:t=fill:"
        f"enable='gte(t,{transition_at:.3f})'",
        # Spotify chrome.
        text("PLAYING FROM YOUR MIX", 150, 34, "0xB3B3B3", 0, duration),
        text(first_title, title_y, 64, "white", 0, transition_at),
        text(first_artist, artist_y, 44, "0xB3B3B3", 0, transition_at),
        text(second_title, title_y, 64, "white", transition_at, duration),
        text(second_artist, artist_y, 44, "0xB3B3B3", transition_at, duration),
        # Progress track and elapsed fill.
        f"drawbox=x=100:y={progress_y}:w=880:h=8:color=0x404040@1:t=fill",
        text("Spotify", 1780, 40, "0x1DB954", 0, duration),
    ])

    run([
        "ffmpeg", "-y", "-v", "error",
        "-i", str(audio_path),
        "-f", "lavfi", "-i",
        f"color=c=0x121212:s={CANVAS_WIDTH}x{CANVAS_HEIGHT}:r=30:d={duration}",
        "-f", "lavfi", "-i", f"color=c=0x1DB954:s=880x8:r=30",
        "-filter_complex",
        f"[0:a]showwaves=s=920x{wave_height}:mode=cline:rate=30:colors=0x1DB954|0x1ED760,"
        f"format=yuva420p,colorkey=0x000000:0.30:0.05[wave];"
        f"[1:v]{background}[bg];"
        f"[bg][2:v]overlay=x='100-880+(880*t/{duration:.3f})':y={progress_y}:"
        f"shortest=0:eof_action=pass[withbar];"
        f"[withbar][wave]overlay=x=80:y={wave_y}:shortest=1[v]",
        "-map", "[v]", "-map", "0:a",
        "-t", f"{duration:.3f}",
        "-c:v", "libx264", "-crf", "20", "-preset", "veryfast", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart",
        str(destination),
    ])


def build_hook_clip(destination: Path, seconds: float = 4.0) -> None:
    """A colourful supporting clip standing in for AI or comedy footage."""
    font = find_font()
    run([
        "ffmpeg", "-y", "-v", "error",
        "-f", "lavfi", "-i",
        f"gradients=s=1080x1920:d={seconds}:r=30:speed=0.25:"
        "c0=0xFF3366:c1=0x1DB954:c2=0x2244FF:c3=0xFFCC00",
        "-vf",
        f"drawtext=fontfile='{font}':text='SAMPLE HOOK CLIP':fontsize=72:fontcolor=white:"
        "x=(w-text_w)/2:y=900:box=1:boxcolor=black@0.45:boxborderw=28,"
        "noise=alls=6:allf=t",
        "-t", f"{seconds}", "-an",
        "-c:v", "libx264", "-crf", "22", "-preset", "veryfast", "-pix_fmt", "yuv420p",
        str(destination),
    ])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="examples/inputs/demo-mix",
                        help="output directory for the fixture")
    parser.add_argument("--first-seconds", type=float, default=13.0)
    parser.add_argument("--second-seconds", type=float, default=16.0)
    parser.add_argument("--blend-seconds", type=float, default=2.0)
    parser.add_argument("--with-hook-clip", action="store_true",
                        help="also generate a supporting clip")
    parser.add_argument("--first-title", default="Night Drive")
    parser.add_argument("--first-artist", default="Lowbeam")
    parser.add_argument("--second-title", default="Paper Lanterns")
    parser.add_argument("--second-artist", default="Ashra Kite")
    args = parser.parse_args()

    if shutil.which("ffmpeg") is None:
        raise SystemExit("ffmpeg is required to generate the fixture.")

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    audio_path = out_dir / "_fixture-audio.wav"
    recording_path = out_dir / "spotify-screen-recording.mp4"

    duration = build_audio(
        audio_path, args.first_seconds, args.second_seconds, args.blend_seconds
    )
    transition_at = args.first_seconds + args.blend_seconds / 2

    build_recording(
        audio_path, recording_path,
        duration=duration,
        transition_at=transition_at,
        first_title=args.first_title,
        first_artist=args.first_artist,
        second_title=args.second_title,
        second_artist=args.second_artist,
    )
    audio_path.unlink(missing_ok=True)
    print(f"wrote {recording_path} ({duration:.1f}s, transition near {transition_at:.1f}s)")

    if args.with_hook_clip:
        hook_path = out_dir / "hook-clip.mp4"
        build_hook_clip(hook_path)
        print(f"wrote {hook_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
