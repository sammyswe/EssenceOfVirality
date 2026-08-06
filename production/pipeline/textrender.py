"""On-screen text: wrapping, size estimation, safe-zone placement and drawtext filters.

FFmpeg's ``drawtext`` centres text exactly at render time using ``text_w``/``text_h``
expressions. The pixel estimates here exist so the planner can check safe zones and
protected regions before a single frame is rendered.
"""

from __future__ import annotations

import textwrap
from pathlib import Path
from typing import Any

from .paths import load_config

# Mean advance width of DejaVu Sans Bold, as a fraction of nominal font size.
# Measured across the ASCII range; used only for bounding-box estimation.
_MEAN_CHAR_WIDTH_RATIO = 0.58
_LINE_HEIGHT_RATIO = 1.22

# drawtext treats these as syntax; they must be escaped in the text value.
_ESCAPES = {
    "\\": r"\\",
    ":": r"\:",
    "'": r"\'",
    "%": r"\%",
}


class TextError(ValueError):
    """Raised when a text cue cannot be placed legibly and safely."""


def resolve_font(font_key: str) -> str:
    """First readable font file for a logical font name."""
    config = load_config("text-styles")
    candidates = (config.get("fonts") or {}).get(font_key) or []
    for candidate in candidates:
        if Path(candidate).is_file():
            return candidate
    for fallback_key, paths in (config.get("fonts") or {}).items():
        for candidate in paths:
            if Path(candidate).is_file():
                return candidate
        del fallback_key
    raise TextError(
        "No usable font found. Install DejaVu or Liberation fonts "
        "(apt install fonts-dejavu-core)."
    )


def get_style(style_name: str) -> dict[str, Any]:
    config = load_config("text-styles")
    styles = config.get("styles") or {}
    if style_name not in styles:
        raise TextError(
            f"Unknown text style {style_name!r}; available: {sorted(styles)}"
        )
    return dict(styles[style_name])


def wrap_text(text: str, style: dict[str, Any]) -> list[str]:
    """Wrap to the style's line budget, preserving explicit newlines."""
    width = int(style.get("max_chars_per_line", 24))
    lines: list[str] = []
    for paragraph in text.split("\n"):
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        lines.extend(textwrap.wrap(paragraph, width=width) or [paragraph])
    return lines or [text]


def estimate_box(
    text: str, style: dict[str, Any], anchor_y: int, canvas_width: int = 1080
) -> dict[str, int]:
    """Estimated pixel bounds of the rendered cue, including any background plate."""
    lines = wrap_text(text, style)
    font_size = int(style.get("font_size", 56))
    padding = int(style.get("box_border", 0)) if style.get("box") else 0
    line_spacing = int(style.get("line_spacing", 0))

    longest = max((len(line) for line in lines), default=0)
    text_width = int(longest * font_size * _MEAN_CHAR_WIDTH_RATIO)
    line_height = int(font_size * _LINE_HEIGHT_RATIO)
    text_height = line_height * len(lines) + line_spacing * max(len(lines) - 1, 0)

    total_width = text_width + padding * 2
    total_height = text_height + padding * 2

    x1 = int((canvas_width - total_width) / 2)
    return {
        "x1": x1,
        "y1": anchor_y,
        "x2": x1 + total_width,
        "y2": anchor_y + total_height,
        "lines": len(lines),
    }


def fit_to_safe_area(
    text: str, style_name: str, anchor_y: int, safe_area: dict[str, int]
) -> tuple[dict[str, Any], dict[str, int]]:
    """Shrink the font until the cue fits the safe text area.

    Returns the (possibly adjusted) style and its estimated box. Raises when the
    text cannot fit even at the minimum legible size — the caller must shorten it
    rather than render something unreadable.
    """
    style = get_style(style_name)
    available_width = safe_area["x_max"] - safe_area["x_min"]
    available_height = safe_area["y_max"] - safe_area["y_min"]
    minimum_font_size = 34

    while True:
        box = estimate_box(text, style, anchor_y)
        width = box["x2"] - box["x1"]
        height = box["y2"] - box["y1"]
        # The box is centred on the canvas, so containment is checked directly
        # rather than clamped: clamping would hide an overflow from the checks.
        fits_width = (
            width <= available_width
            and box["x1"] >= safe_area["x_min"]
            and box["x2"] <= safe_area["x_max"]
        )
        fits_height = height <= available_height and box["y2"] <= safe_area["y_max"]
        if fits_width and fits_height:
            return style, box
        if style["font_size"] <= minimum_font_size:
            raise TextError(
                f"text {text!r} cannot fit the safe area at a legible size "
                f"(needs {width}x{height}px, {available_width}x{available_height}px "
                "available) — shorten it"
            )
        style["font_size"] = max(minimum_font_size, int(style["font_size"] * 0.9))
        style["max_chars_per_line"] = int(style.get("max_chars_per_line", 24) * 1.08)


def escape_drawtext(value: str) -> str:
    out = []
    for char in value:
        out.append(_ESCAPES.get(char, char))
    return "".join(out)


def _colour_with_alpha(colour: str, alpha: float | None) -> str:
    if alpha is None:
        return colour
    return f"{colour}@{alpha:.3f}"


def build_drawtext(
    cue_text: str,
    style: dict[str, Any],
    *,
    y: int,
    start: float,
    end: float,
    animation: str = "fade",
    canvas_width: int = 1080,
) -> str:
    """Build a single ``drawtext`` filter string for one cue.

    Multi-line text is emitted as one drawtext per line so that line spacing and
    per-line centring stay under our control.
    """
    del canvas_width  # centring uses ffmpeg's own text_w, no width needed here

    font_file = resolve_font(str(style.get("font", "sans_bold")))
    font_size = int(style.get("font_size", 56))
    line_spacing = int(style.get("line_spacing", 0))
    line_height = int(font_size * _LINE_HEIGHT_RATIO)
    lines = wrap_text(cue_text, style)

    fade = 0.0
    if animation in {"fade", "pop"}:
        config = load_config("text-styles")
        fade = float(
            ((config.get("animations") or {}).get(animation) or {}).get("fade_seconds", 0.25)
        )
        # Never let the ramp consume more than a third of the visible window.
        fade = min(fade, max((end - start) / 3.0, 0.0))

    if fade > 0:
        alpha = (
            f"if(lt(t,{start:.3f}),0,"
            f"if(lt(t,{start + fade:.3f}),(t-{start:.3f})/{fade:.3f},"
            f"if(lt(t,{end - fade:.3f}),1,"
            f"if(lt(t,{end:.3f}),({end:.3f}-t)/{fade:.3f},0))))"
        )
    else:
        alpha = "1"

    filters: list[str] = []
    for index, line in enumerate(lines):
        line_y = y + index * (line_height + line_spacing)
        parts = [
            f"fontfile='{font_file}'",
            f"text='{escape_drawtext(line)}'",
            f"fontsize={font_size}",
            f"fontcolor={_colour_with_alpha(str(style.get('colour', '#FFFFFF')), None)}",
            "x=(w-text_w)/2",
            f"y={line_y}",
            f"alpha='{alpha}'",
            f"enable='between(t,{start:.3f},{end:.3f})'",
        ]
        if style.get("box"):
            parts.append("box=1")
            parts.append(
                f"boxcolor={_colour_with_alpha(str(style.get('box_colour', '#000000')), float(style.get('box_opacity', 0.4)))}"
            )
            parts.append(f"boxborderw={int(style.get('box_border', 24))}")
        border_width = int(style.get("border_width", 0) or 0)
        if border_width:
            parts.append(f"borderw={border_width}")
            parts.append(f"bordercolor={style.get('border_colour', '#000000')}")
        shadow = style.get("shadow") or {}
        if shadow:
            parts.append(f"shadowx={int(shadow.get('x', 0))}")
            parts.append(f"shadowy={int(shadow.get('y', 0))}")
            parts.append(f"shadowcolor={shadow.get('colour', '#000000AA')}")
        filters.append("drawtext=" + ":".join(parts))

    return ",".join(filters)


def safe_area() -> dict[str, int]:
    zones = load_config("safe-zones")
    return {key: int(value) for key, value in (zones.get("text_area") or {}).items()}


def anchor_for(role: str) -> tuple[int, str]:
    zones = load_config("safe-zones")
    anchors = zones.get("anchors") or {}
    entry = anchors.get(role) or anchors.get("hook") or {"y": 380, "align": "center"}
    return int(entry.get("y", 380)), str(entry.get("align", "center"))
