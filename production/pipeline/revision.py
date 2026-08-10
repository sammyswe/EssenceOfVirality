"""Applying feedback directives to an edit plan.

The revision engine never edits a rendered file. It adjusts the plan and the job's
effective configuration, then the pipeline renders again from the original source —
so every revision is reproducible from the job folder plus its feedback history.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .feedback import Directive
from .paths import deep_merge


@dataclass
class RevisionAdjustments:
    """Overrides derived from feedback, applied before planning the next render."""

    config_overrides: dict[str, Any] = field(default_factory=dict)
    format_override: str | None = None
    drop_secondary: bool = False
    secondary_factor: float | None = None
    avoid_hook: str | None = None
    avoid_cta: str | None = None
    remove_text: bool = False
    rewrite_caption_register: str | None = None
    applied: list[dict[str, str]] = field(default_factory=list)
    unsupported: list[dict[str, str]] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "config_overrides": self.config_overrides,
            "format_override": self.format_override,
            "drop_secondary": self.drop_secondary,
            "secondary_factor": self.secondary_factor,
            "avoid_hook": self.avoid_hook,
            "avoid_cta": self.avoid_cta,
            "remove_text": self.remove_text,
            "rewrite_caption_register": self.rewrite_caption_register,
            "applied": self.applied,
            "unsupported": self.unsupported,
        }


def build_adjustments(
    directives: list[Directive],
    *,
    current_config: dict[str, Any],
    previous_hook: str = "",
    previous_cta: str = "",
) -> RevisionAdjustments:
    """Translate directives into concrete configuration and planning overrides."""
    adjustments = RevisionAdjustments()
    overrides: dict[str, Any] = {}

    layout_cfg = current_config.get("layout", {})
    duration_cfg = current_config.get("duration", {})
    emphasis_cfg = current_config.get("transition", {}).get("emphasis", {})

    for directive in directives:
        action = directive.action
        params = directive.parameters or {}

        if action == "increase_spotify_area":
            step = float(params.get("step", 0.08))
            # Two levers: the band height in split layouts, and how far the capture
            # is cropped towards its song labels and waveform. The second is what
            # makes the surface larger in a full-bleed layout, where the band
            # fraction does nothing.
            band = float(layout_cfg.get("split_spotify_fraction", 0.62))
            new_band = min(0.85, band + step)
            zoom = float(layout_cfg.get("spotify_content_zoom", 0.0))
            # The zoom is a fraction of the distance to the tightest crop the song
            # labels and waveform allow, so a request moves a large share of it —
            # small nudges are invisible when that distance is short.
            new_zoom = min(1.0, zoom + float(params.get("zoom_step", 0.4)))
            overrides = deep_merge(overrides, {
                "layout": {
                    "split_spotify_fraction": new_band,
                    "spotify_content_zoom": new_zoom,
                }
            })
            adjustments.applied.append({
                "action": action,
                "effect": f"split band {band:.2f} -> {new_band:.2f}, content zoom "
                          f"{zoom:.2f} -> {new_zoom:.2f}",
                "trigger": directive.trigger_phrase,
            })

        elif action == "decrease_spotify_area":
            step = float(params.get("step", 0.06))
            band = float(layout_cfg.get("split_spotify_fraction", 0.62))
            floor = float(layout_cfg.get("min_spotify_area_fraction", 0.45))
            new_band = max(floor, band - step)
            zoom = float(layout_cfg.get("spotify_content_zoom", 0.0))
            new_zoom = max(0.0, zoom - float(params.get("zoom_step", 0.4)))
            overrides = deep_merge(overrides, {
                "layout": {
                    "split_spotify_fraction": new_band,
                    "spotify_content_zoom": new_zoom,
                }
            })
            adjustments.applied.append({
                "action": action,
                "effect": f"split band {band:.2f} -> {new_band:.2f}, content zoom "
                          f"{zoom:.2f} -> {new_zoom:.2f} "
                          f"(floor {floor:.2f} protects Spotify recognisability)",
                "trigger": directive.trigger_phrase,
            })

        elif action == "shorten_lead_in":
            seconds = float(params.get("seconds", 2.0))
            # The cap alone is not enough: a template usually asks for less than the
            # cap already, so the adjustment is applied to whatever it asks for.
            cap = float(duration_cfg.get("max_pre_transition_seconds", 12.0))
            new_cap = max(2.0, cap - seconds)
            current = float(duration_cfg.get("lead_in_adjustment_seconds", 0.0))
            new_adjustment = max(-8.0, current - seconds)
            overrides = deep_merge(overrides, {
                "duration": {
                    "max_pre_transition_seconds": new_cap,
                    "lead_in_adjustment_seconds": new_adjustment,
                }
            })
            adjustments.applied.append({
                "action": action,
                "effect": f"lead-in cap {cap:.1f}s -> {new_cap:.1f}s and template "
                          f"lead-in adjusted by {new_adjustment:+.1f}s",
                "trigger": directive.trigger_phrase,
            })

        elif action == "shorten_output":
            seconds = float(params.get("seconds", 4.0))
            current = float(duration_cfg.get("maximum_seconds", 45.0))
            minimum = float(duration_cfg.get("minimum_seconds", 15.0))
            new_value = max(minimum + 2.0, current - seconds)
            overrides = deep_merge(overrides, {"duration": {"maximum_seconds": new_value}})
            adjustments.applied.append({
                "action": action,
                "effect": f"maximum duration {current:.1f}s -> {new_value:.1f}s",
                "trigger": directive.trigger_phrase,
            })

        elif action == "lengthen_output":
            seconds = float(params.get("seconds", 4.0))
            current = float(duration_cfg.get("minimum_seconds", 15.0))
            maximum = float(duration_cfg.get("maximum_seconds", 45.0))
            new_value = min(maximum - 2.0, current + seconds)
            overrides = deep_merge(overrides, {"duration": {"minimum_seconds": new_value}})
            adjustments.applied.append({
                "action": action,
                "effect": f"minimum duration {current:.1f}s -> {new_value:.1f}s",
                "trigger": directive.trigger_phrase,
            })

        elif action == "disable_zoom":
            overrides = deep_merge(overrides, {
                "transition": {"emphasis": {"enabled": False}}
            })
            adjustments.applied.append({
                "action": action,
                "effect": "zoom emphasis disabled",
                "trigger": directive.trigger_phrase,
            })

        elif action == "increase_emphasis":
            step = float(params.get("amount_step", 0.05))
            current = float(emphasis_cfg.get("zoom_amount", 0.08))
            new_value = min(0.24, current + step)
            overrides = deep_merge(overrides, {
                "transition": {"emphasis": {"enabled": True, "zoom_amount": new_value}}
            })
            adjustments.applied.append({
                "action": action,
                "effect": f"zoom amount {current:.2f} -> {new_value:.2f}",
                "trigger": directive.trigger_phrase,
            })

        elif action == "disable_progress_bar":
            overrides = deep_merge(overrides, {"progress_bar": {"enabled": False}})
            adjustments.applied.append({
                "action": action,
                "effect": "progress bar removed",
                "trigger": directive.trigger_phrase,
            })

        elif action == "remove_secondary":
            adjustments.drop_secondary = True
            adjustments.applied.append({
                "action": action,
                "effect": "supporting clips dropped; the edit falls back to the Spotify surface",
                "trigger": directive.trigger_phrase,
            })

        elif action == "shorten_secondary":
            adjustments.secondary_factor = float(params.get("factor", 0.6))
            adjustments.applied.append({
                "action": action,
                "effect": f"supporting clip windows scaled to "
                          f"{adjustments.secondary_factor:.0%} of their planned length",
                "trigger": directive.trigger_phrase,
            })

        elif action == "regenerate_hook":
            adjustments.avoid_hook = previous_hook
            adjustments.applied.append({
                "action": action,
                "effect": f"hook {previous_hook!r} excluded from the next selection",
                "trigger": directive.trigger_phrase,
            })

        elif action == "regenerate_cta":
            adjustments.avoid_cta = previous_cta
            adjustments.applied.append({
                "action": action,
                "effect": f"call to action {previous_cta!r} excluded from the next selection",
                "trigger": directive.trigger_phrase,
            })

        elif action == "remove_text":
            adjustments.remove_text = True
            adjustments.applied.append({
                "action": action,
                "effect": "all on-screen text removed",
                "trigger": directive.trigger_phrase,
            })

        elif action == "change_format":
            requested = params.get("format")
            if requested:
                adjustments.format_override = str(requested)
                adjustments.applied.append({
                    "action": action,
                    "effect": f"format forced to {requested}",
                    "trigger": directive.trigger_phrase,
                })

        elif action == "rewrite_caption":
            adjustments.rewrite_caption_register = str(params.get("register", "plain"))
            adjustments.applied.append({
                "action": action,
                "effect": "caption rewritten in a plainer register",
                "trigger": directive.trigger_phrase,
            })

        elif action in {"keep_text_style", "keep_format"}:
            adjustments.applied.append({
                "action": action,
                "effect": "recorded as a preference proposal; no change to this render",
                "trigger": directive.trigger_phrase,
            })

        else:
            adjustments.unsupported.append({
                "action": action,
                "reason": "no implementation for this directive",
                "trigger": directive.trigger_phrase,
            })

    adjustments.config_overrides = overrides
    return adjustments


def apply_to_plan(plan, adjustments: RevisionAdjustments) -> None:
    """Apply the adjustments that act on an already-built plan, in place."""
    if adjustments.drop_secondary and plan.secondary_clips:
        dropped = [clip.label for clip in plan.secondary_clips]
        plan.secondary_clips = []
        plan.add_decision(
            "dropped supporting clips",
            f"creator feedback removed {', '.join(dropped)}",
            stage="revision",
        )

    if adjustments.secondary_factor and plan.secondary_clips:
        factor = adjustments.secondary_factor
        for clip in plan.secondary_clips:
            length = (clip.end_seconds - clip.start_seconds) * factor
            clip.end_seconds = round(clip.start_seconds + max(length, 0.6), 3)
        plan.add_decision(
            f"supporting clips shortened to {factor:.0%}",
            "creator feedback said the clip competed with the transition",
            stage="revision",
        )

    if adjustments.remove_text and plan.text_cues:
        plan.text_cues = []
        plan.hook_text = ""
        plan.cta_text = ""
        plan.add_decision(
            "removed all on-screen text",
            "creator feedback asked for no text overlays",
            stage="revision",
        )

    for entry in adjustments.applied:
        plan.add_decision(
            f"revision: {entry['action']}",
            f"{entry['effect']} (triggered by {entry['trigger']!r})",
            stage="revision",
        )
    for entry in adjustments.unsupported:
        plan.warnings.append(
            f"feedback {entry['trigger']!r} could not be applied automatically: "
            f"{entry['reason']}"
        )
