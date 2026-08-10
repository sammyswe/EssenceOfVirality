"""Skills 2 and 3 — creative direction and retention editing.

Chooses a format family, works out the source window around the transition, places
the Spotify surface and any supporting clips, and writes the text cues. Everything
it decides is recorded with a rationale so a later revision can argue with it.

Two invariants drive the timing maths:
  * the transition region is never cut or sped up;
  * the Spotify surface never drops below the configured share of the frame.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any

from . import preferences as prefs
from . import textrender
from .editplan import (
    AudioPlan,
    EditPlan,
    Emphasis,
    ExperimentPlan,
    Placement,
    SecondaryClip,
    TextCue,
)
from .inspector import InputReport, Region, protected_regions_for
from .jobspec import JobSpec
from .paths import load_config, load_templates

CANVAS_WIDTH = 1080
CANVAS_HEIGHT = 1920


class CreativeError(RuntimeError):
    """Raised when no valid plan can be produced from the supplied inputs."""


@dataclass
class FormatChoice:
    name: str
    family: str
    template: dict[str, Any]
    score: float
    reasons: list[str]
    rejected: list[dict[str, str]]


def _usable_assets(report: InputReport) -> list[Any]:
    return [asset for asset in report.assets if asset.usable]


def _stable_choice(options: list[str], seed: str) -> str:
    """Deterministic rotation so repeated jobs do not reuse the same wording."""
    digest = hashlib.sha256(seed.encode("utf-8")).digest()
    return options[digest[0] % len(options)]


def choose_format(
    job: JobSpec, report: InputReport, resolved: prefs.ResolvedPreferences
) -> FormatChoice:
    """Pick the format family that the available assets and preferences support."""
    templates = load_templates()
    usable = _usable_assets(report)
    asset_count = len(usable)

    requested = job.preferred_format
    if requested and requested != "auto":
        template = templates.get(requested)
        if template is None:
            raise CreativeError(
                f"job requested format {requested!r}; available: {sorted(templates)}"
            )
        needs = template.get("requires") or {}
        minimum = int(needs.get("minimum_supporting_assets", 0))
        if asset_count < minimum:
            raise CreativeError(
                f"format {requested!r} needs at least {minimum} supporting clip(s); "
                f"{asset_count} usable clip(s) supplied"
            )
        return FormatChoice(
            name=requested,
            family=str(template.get("family", requested)),
            template=template,
            score=1.0,
            reasons=[f"format requested in job.yaml: {requested}"],
            rejected=[],
        )

    mood = job.mood.lower()
    avoided = set(resolved.avoided_formats)
    preferred = resolved.get("preferred_format")

    scored: list[tuple[float, str, dict[str, Any], list[str]]] = []
    rejected: list[dict[str, str]] = []

    for name, template in sorted(templates.items()):
        needs = template.get("requires") or {}
        minimum = int(needs.get("minimum_supporting_assets", 0))
        maximum = int(needs.get("maximum_supporting_assets", 99))
        reasons: list[str] = []

        if name in avoided:
            rejected.append({"format": name, "reason": "creator preference avoids this format"})
            continue
        if asset_count < minimum:
            rejected.append({
                "format": name,
                "reason": f"needs {minimum} supporting clip(s), {asset_count} available",
            })
            continue

        score = 1.0
        # Prefer a family that uses what was actually supplied.
        if minimum <= asset_count <= maximum:
            score += 0.6
            if asset_count:
                reasons.append(f"uses the {asset_count} supplied clip(s)")
        if asset_count == 0 and minimum == 0:
            score += 0.4
            reasons.append("works from the Spotify recording alone")

        if preferred == name:
            score += 1.2
            reasons.append("matches an approved creator preference")

        if mood:
            haystack = f"{name} {template.get('description', '')}".lower()
            if mood in haystack:
                score += 0.5
                reasons.append(f"matches the requested mood {mood!r}")
            if mood in {"funny", "comedy", "humour", "humor"} and name == "comedy-hook":
                score += 0.8
                reasons.append("comedy mood requested and a hook clip is available")

        # Contrast-dependent families need evidence that the tracks differ.
        if (template.get("constraints") or {}).get("requires_track_contrast"):
            if not _tracks_contrast_known(job):
                rejected.append({
                    "format": name,
                    "reason": "hook asserts the tracks clash, but no track metadata "
                              "confirms a contrast — would risk a false claim",
                })
                continue
            score += 0.3
            reasons.append("track metadata supports a genuine contrast claim")

        scored.append((score, name, template, reasons))

    if not scored:
        raise CreativeError(
            "no format family fits the supplied assets; add a supporting clip or "
            "set creative_direction.preferred_format to clean-showcase"
        )

    scored.sort(key=lambda entry: (-entry[0], entry[1]))
    score, name, template, reasons = scored[0]
    if not reasons:
        reasons.append("highest-scoring family for the available inputs")
    return FormatChoice(
        name=name,
        family=str(template.get("family", name)),
        template=template,
        score=score,
        reasons=reasons,
        rejected=rejected,
    )


def _tracks_contrast_known(job: JobSpec) -> bool:
    """Only claim a contrast when the job states both tracks and they differ."""
    first = (job.tracks.get("first") or {})
    second = (job.tracks.get("second") or {})
    if not first.get("title") or not second.get("title"):
        return False
    genres = {
        str(first.get("genre", "")).strip().lower(),
        str(second.get("genre", "")).strip().lower(),
    }
    if "" in genres:
        # Without genres, fall back to an explicit creator statement.
        return bool(job.creative_direction.get("tracks_contrast"))
    return len(genres) > 1


@dataclass
class Timing:
    source_in: float
    source_out: float
    duration: float
    transition_output: float
    transition_window: tuple[float, float]
    notes: list[str]


def plan_timing(
    job: JobSpec, report: InputReport, template: dict[str, Any]
) -> Timing:
    """Choose the source window around the transition.

    Never places a cut inside the transition region, and prefers the template's
    lead-in/tail shape when the recording is long enough to allow a choice.
    """
    config = job.config
    duration_cfg = config["duration"]
    source_duration = float(report.spotify.get("duration_seconds") or 0.0)
    if source_duration <= 0:
        raise CreativeError("Spotify recording has no measurable duration")

    transition = report.transition or {}
    transition_at = float(transition.get("seconds", source_duration / 2))
    window_start = float(transition.get("start_seconds", max(0.0, transition_at - 1.2)))
    window_end = float(transition.get("end_seconds", min(source_duration, transition_at + 2.0)))

    pacing = template.get("pacing") or {}
    want_lead = float(pacing.get("preferred_lead_in_seconds",
                                 duration_cfg["max_pre_transition_seconds"]))
    want_tail = float(pacing.get("preferred_tail_seconds",
                                 duration_cfg["post_transition_seconds"]))
    want_lead = min(want_lead, float(duration_cfg["max_pre_transition_seconds"]))
    adjustment = float(duration_cfg.get("lead_in_adjustment_seconds", 0.0) or 0.0)
    if adjustment:
        want_lead = max(1.5, want_lead + adjustment)

    minimum = float(duration_cfg["minimum_seconds"])
    maximum = float(duration_cfg["maximum_seconds"])
    notes: list[str] = []

    lead = min(want_lead, transition_at)
    tail = min(want_tail, source_duration - transition_at)

    # Grow towards the minimum duration using whatever side has material left.
    total = lead + tail
    if total < minimum:
        spare_lead = transition_at - lead
        spare_tail = (source_duration - transition_at) - tail
        needed = minimum - total
        take_tail = min(spare_tail, needed)
        tail += take_tail
        needed -= take_tail
        if needed > 0:
            take_lead = min(spare_lead, needed)
            lead += take_lead
            needed -= take_lead
        if needed > 0:
            notes.append(
                f"recording is only {source_duration:.1f}s, so the edit is "
                f"{lead + tail:.1f}s — below the {minimum:.0f}s minimum. Record more "
                "material after the transition to reach the target window."
            )

    # Trim towards the maximum, taking from the lead-in first: the payoff matters more.
    total = lead + tail
    if total > maximum:
        excess = total - maximum
        take_lead = min(excess, max(lead - 2.0, 0.0))
        lead -= take_lead
        excess -= take_lead
        if excess > 0:
            tail = max(tail - excess, 2.0)
        notes.append(
            f"trimmed to the {maximum:.0f}s maximum by shortening the lead-in first"
        )

    source_in = max(0.0, transition_at - lead)
    source_out = min(source_duration, transition_at + tail)

    # Hard rule: the cut may not land inside the transition region.
    if source_in > window_start:
        source_in = max(0.0, window_start - 0.5)
        notes.append("lead-in extended so the cut sits before the transition region")
    if source_out < window_end:
        source_out = min(source_duration, window_end + 0.5)
        notes.append("tail extended so the cut sits after the transition region")

    duration = source_out - source_in
    if duration <= 0:
        raise CreativeError("computed a zero-length edit; check transition.seconds")

    return Timing(
        source_in=source_in,
        source_out=source_out,
        duration=duration,
        transition_output=transition_at - source_in,
        transition_window=(window_start - source_in, window_end - source_in),
        notes=notes,
    )


def _spotify_placement(template: dict[str, Any], resolved: prefs.ResolvedPreferences) -> Placement:
    layout = template.get("layout") or {}
    mode = str(layout.get("mode", "full"))

    if mode == "split":
        fraction = float(resolved.get("spotify_fraction", layout.get("spotify_fraction", 0.62)))
        fraction = max(0.55, min(fraction, 0.80))
        height = int(CANVAS_HEIGHT * fraction) // 2 * 2
        position = str(layout.get("spotify_position", "bottom"))
        y = CANVAS_HEIGHT - height if position == "bottom" else 0
        return Placement(x=0, y=y, width=CANVAS_WIDTH, height=height)

    return Placement(x=0, y=0, width=CANVAS_WIDTH, height=CANVAS_HEIGHT)


def _inset_placement(
    template: dict[str, Any],
    resolved: prefs.ResolvedPreferences,
    protected: list[Any],
) -> Placement:
    layout = template.get("layout") or {}
    scale = float(resolved.get("pip_scale", layout.get("pip_scale", 0.34)))
    scale = max(0.2, min(scale, 0.5))
    margin = int(layout.get("pip_margin", 48))
    corner = str(resolved.get("pip_corner", layout.get("pip_corner", "top_right")))

    width = int(CANVAS_WIDTH * scale) // 2 * 2
    height = int(width * 16 / 9) // 2 * 2
    if height > CANVAS_HEIGHT * 0.4:
        height = int(CANVAS_HEIGHT * 0.4) // 2 * 2
        width = int(height * 9 / 16) // 2 * 2

    corners = {
        "top_left": (margin, margin),
        "top_right": (CANVAS_WIDTH - width - margin, margin),
        "bottom_left": (margin, CANVAS_HEIGHT - height - margin),
        "bottom_right": (CANVAS_WIDTH - width - margin, CANVAS_HEIGHT - height - margin),
    }
    x, y = corners.get(corner, corners["top_right"])

    # Move the inset away from any protected Spotify region it would cover.
    def overlaps(px: int, py: int) -> bool:
        for region in protected:
            if not (
                px + width <= region.x1 or px >= region.x2
                or py + height <= region.y1 or py >= region.y2
            ):
                return True
        return False

    if overlaps(x, y):
        for candidate_name, (cx, cy) in corners.items():
            if not overlaps(cx, cy):
                x, y = cx, cy
                del candidate_name
                break

    return Placement(x=x, y=y, width=width, height=height)


def _fill_template(text: str, job: JobSpec) -> str | None:
    """Substitute track fields; return None when a required field is missing."""
    first = job.tracks.get("first") or {}
    second = job.tracks.get("second") or {}
    values = {
        "first_track": str(first.get("title", "") or ""),
        "first_artist": str(first.get("artist", "") or ""),
        "second_track": str(second.get("title", "") or ""),
        "second_artist": str(second.get("artist", "") or ""),
    }
    try:
        filled = text.format(**values)
    except (KeyError, IndexError):
        return None
    if "{" in filled or any(
        placeholder in text and not values[placeholder]
        for placeholder in values
        if "{" + placeholder + "}" in text
    ):
        return None
    return filled


def choose_hook(
    job: JobSpec, report: InputReport, template: dict[str, Any]
) -> tuple[str, str]:
    """Pick a hook whose claim the video can actually keep.

    Returns (text, rationale). Patterns requiring track fields or an asserted
    truth are skipped unless the job supplies the evidence.
    """
    override = (job.creative_direction.get("hook") or "").strip()
    if override:
        return override, "hook supplied in job.yaml"

    candidates: list[tuple[str, str]] = []
    for pattern in template.get("hook_patterns") or []:
        text = str(pattern.get("text", "")).strip()
        if not text:
            continue
        required_fields = pattern.get("requires_fields") or []
        if required_fields:
            filled = _fill_template(text, job)
            if filled is None:
                continue
            text = filled
        elif "{" in text:
            filled = _fill_template(text, job)
            if filled is None:
                continue
            text = filled

        assertion = pattern.get("requires_true")
        if assertion and not _tracks_contrast_known(job):
            # The claim cannot be verified from the job, so it is not used.
            continue

        candidates.append((text, str(pattern.get("kind", "unspecified"))))

    if not candidates:
        return (
            "wait for the switch",
            "no template hook had its preconditions met; used the neutral "
            "anticipation cue, which is true of every mix video",
        )

    seed = f"{job.job_id}:{template.get('name')}:hook"
    chosen_text = _stable_choice([text for text, _ in candidates], seed)
    kind = next(kind for text, kind in candidates if text == chosen_text)
    return chosen_text, f"selected {kind!r} hook from {len(candidates)} valid candidates"


def choose_cta(job: JobSpec, template: dict[str, Any]) -> tuple[str, str]:
    override = (job.creative_direction.get("cta") or "").strip()
    if override:
        return override, "call to action supplied in job.yaml"
    patterns = template.get("cta_patterns") or []
    if not patterns:
        return "rate this transition", "template defined no call to action; used the default"
    texts = [str(entry.get("text", "")).strip() for entry in patterns if entry.get("text")]
    seed = f"{job.job_id}:{template.get('name')}:cta"
    chosen = _stable_choice(texts, seed)
    intent = next(
        (str(entry.get("intent", "")) for entry in patterns if entry.get("text") == chosen),
        "",
    )
    return chosen, f"selected call to action with intent {intent!r}"


def _build_text_cues(
    job: JobSpec,
    template: dict[str, Any],
    timing: Timing,
    hook_text: str,
    cta_text: str,
    protected: list[Any],
    resolved: prefs.ResolvedPreferences,
    secondary: list[SecondaryClip] | None = None,
) -> tuple[list[TextCue], list[str]]:
    config = job.config
    styles = template.get("text_styles") or {}
    safe = textrender.safe_area()
    warnings: list[str] = []
    cues: list[TextCue] = []

    hard = [region for region in protected if region.enforcement == "hard"]

    # A picture-in-picture inset is opaque, so text underneath it is unreadable.
    # Treat it as another region text must clear.
    for clip in secondary or []:
        if clip.mode == "inset" and clip.placement is not None:
            hard.append(Region(
                name=f"inset:{clip.label}",
                x1=clip.placement.x,
                y1=clip.placement.y,
                x2=clip.placement.x + clip.placement.width,
                y2=clip.placement.y + clip.placement.height,
                enforcement="hard",
            ))

    def clears(box: dict[str, int], regions: list[Any]) -> list[str]:
        """Names of regions the box overlaps."""
        hits: list[str] = []
        for region in regions:
            overlaps = not (
                box["x2"] <= region.x1 or box["x1"] >= region.x2
                or box["y2"] <= region.y1 or box["y1"] >= region.y2
            )
            if overlaps:
                hits.append(region.name)
        return hits

    def add(role: str, text: str, style_name: str, start: float, end: float,
            rationale: str) -> None:
        if not text:
            return
        anchor_y, align = textrender.anchor_for(role)
        try:
            style, box = textrender.fit_to_safe_area(text, style_name, anchor_y, safe)
        except textrender.TextError as exc:
            warnings.append(f"dropped {role} text: {exc}")
            return

        height = box["y2"] - box["y1"]
        gap = 24

        # Text may never cover song information or the waveform. Search for the
        # position closest to the intended anchor that clears every hard region.
        if clears(box, hard):
            candidates = [safe["y_min"]]
            for region in hard:
                candidates.append(region.y1 - height - gap)
                candidates.append(region.y2 + gap)
            candidates = [
                candidate for candidate in candidates
                if safe["y_min"] <= candidate and candidate + height <= safe["y_max"]
            ]
            candidates.sort(key=lambda value: abs(value - anchor_y))

            placed = False
            for candidate in candidates:
                trial = textrender.estimate_box(text, style, candidate)
                if not clears(trial, hard):
                    if candidate != anchor_y:
                        warnings.append(
                            f"{role} text moved from y={anchor_y} to y={candidate} to "
                            f"clear the {', '.join(clears(box, hard))} region(s)"
                        )
                    anchor_y, box, placed = candidate, trial, True
                    break
            if not placed:
                warnings.append(
                    f"dropped {role} text {text!r}: no position inside the safe area "
                    f"clears the {', '.join(clears(box, hard))} region(s)"
                )
                return

        soft_hits = clears(box, [r for r in protected if r.enforcement == "soft"])
        if soft_hits:
            rationale += (
                f" (sits over {', '.join(soft_hits)}, which is permitted but noted)"
            )

        cues.append(TextCue(
            id=f"{role}-{len(cues) + 1}",
            text=text,
            role=role,
            style=style_name,
            start_seconds=round(max(start, 0.0), 3),
            end_seconds=round(min(end, timing.duration), 3),
            y=anchor_y,
            align=align,
            animation="fade",
            box=box,
            rationale=rationale,
        ))

    hook_cfg = config["hook"]
    hook_start = float(hook_cfg["display_start_seconds"])
    hook_end = min(
        hook_start + float(hook_cfg["display_seconds"]),
        max(timing.transition_window[0] - 0.4, hook_start + 1.0),
    )
    add(
        "hook", hook_text, str(styles.get("hook", "sleek")), hook_start, hook_end,
        "opening promise; clears the transition window so the payoff is uncontested",
    )

    # Curiosity formats must resolve their question at the transition.
    constraints = template.get("constraints") or {}
    if constraints.get("reveal_required"):
        reveal_text = ""
        for pattern in template.get("reveal_patterns") or []:
            candidate = _fill_template(str(pattern.get("text", "")), job)
            if candidate:
                reveal_text = candidate
                break
        if not reveal_text:
            reveal_text = "there it is"
        window = float(constraints.get("reveal_within_seconds_of_transition", 1.5))
        add(
            "secondary", reveal_text, str(styles.get("reveal", "spotify_accent")),
            timing.transition_output, timing.transition_output + window + 1.0,
            "closes the curiosity gap opened by the hook, at the moment it is answered",
        )

    if config["cta"]["enabled"] and cta_text:
        lead = float(config["cta"]["lead_seconds"])
        cta_start = max(timing.transition_window[1] + 0.6, timing.duration - lead)
        cta_end = min(cta_start + float(config["cta"]["display_seconds"]), timing.duration)
        if cta_end - cta_start >= 1.0:
            add(
                "cta", cta_text, str(styles.get("cta", "question")), cta_start, cta_end,
                "appears after the payoff so it never competes with the transition",
            )
        else:
            warnings.append(
                "no room for a call to action after the transition; the edit ends too "
                "soon after the blend"
            )

    if "hook_text" in resolved.banned_devices:
        cues = [cue for cue in cues if cue.role != "hook"]
        warnings.append("hook text removed by an approved creator preference")

    return cues, warnings


def _plan_secondary(
    job: JobSpec,
    report: InputReport,
    template: dict[str, Any],
    timing: Timing,
    resolved: prefs.ResolvedPreferences,
    protected: list[Any],
) -> tuple[list[SecondaryClip], list[str]]:
    layout = template.get("layout") or {}
    mode = str(layout.get("mode", "full"))
    constraints = template.get("constraints") or {}
    usable = _usable_assets(report)
    warnings: list[str] = []
    clips: list[SecondaryClip] = []

    if mode == "full" or not usable:
        return clips, warnings

    blend_start, blend_end = timing.transition_window

    if mode == "hook_cutaway":
        hook_asset = next(
            (asset for asset in usable if asset.role == "hook"), usable[0]
        )
        wanted = float(layout.get("hook_seconds", 2.2))
        cap = float(layout.get("maximum_hook_seconds", 3.5))
        margin = float(layout.get("minimum_margin_before_transition_seconds", 3.0))
        limit = max(0.8, min(cap, blend_start - margin))
        length = min(wanted, limit, hook_asset.duration_seconds)

        visible_by = float(constraints.get("spotify_visible_by_seconds", 4.0))
        if length > visible_by:
            length = visible_by
            warnings.append(
                f"hook cutaway shortened to {length:.1f}s so the Spotify surface "
                "appears early enough to explain the video"
            )
        if length < 0.8:
            warnings.append(
                "no room for a hook cutaway before the transition; falling back to the "
                "Spotify surface alone"
            )
        else:
            clips.append(SecondaryClip(
                path=hook_asset.path,
                label=hook_asset.label,
                role="hook",
                mode="cutaway",
                placement=Placement(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT),
                start_seconds=0.0,
                end_seconds=round(length, 3),
                loop=False,
                rationale="full-screen opening; hands over to Spotify before the blend",
            ))

        payoff_seconds = float(layout.get("payoff_cutaway_seconds", 0.0))
        payoff_asset = next((asset for asset in usable if asset.role == "payoff"), None)
        if payoff_asset and payoff_seconds > 0:
            start = blend_end + 0.3
            end = min(start + payoff_seconds, timing.duration - 0.5)
            if end - start >= 0.6:
                clips.append(SecondaryClip(
                    path=payoff_asset.path,
                    label=payoff_asset.label,
                    role="payoff",
                    mode="cutaway",
                    placement=Placement(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT),
                    start_seconds=round(start, 3),
                    end_seconds=round(end, 3),
                    loop=False,
                    rationale="brief resolution shot after the blend has landed",
                ))
        return clips, warnings

    asset = next(
        (item for item in usable if item.role in {"overlay", "unassigned"}), usable[0]
    )

    if mode == "split":
        placement = _spotify_placement(template, resolved)
        band_height = CANVAS_HEIGHT - placement.height
        clips.append(SecondaryClip(
            path=asset.path,
            label=asset.label,
            role="overlay",
            mode="band",
            placement=Placement(0, 0, CANVAS_WIDTH, band_height),
            start_seconds=0.0,
            end_seconds=timing.duration,
            loop=bool(layout.get("loop_secondary", True)),
            rationale="upper band supplies motion without covering the Spotify surface",
        ))
        return clips, warnings

    if mode == "pip":
        placement = _inset_placement(template, resolved, protected)
        start = float(layout.get("inset_start_seconds", 0.0))
        end = timing.duration
        if layout.get("hide_during_transition", True):
            end = max(start + 0.5, blend_start - 0.3)
        clips.append(SecondaryClip(
            path=asset.path,
            label=asset.label,
            role="overlay",
            mode="inset",
            placement=placement,
            start_seconds=round(start, 3),
            end_seconds=round(end, 3),
            loop=bool(layout.get("loop_secondary", True)),
            rationale=(
                "corner inset for motion; removed before the blend so nothing competes "
                "with the payoff"
            ),
        ))
        return clips, warnings

    warnings.append(f"layout mode {mode!r} not implemented; rendering Spotify alone")
    return clips, warnings


def build_plan(
    job: JobSpec,
    report: InputReport,
    *,
    revision: int = 1,
    format_override: str | None = None,
    research_refs: list[str] | None = None,
) -> EditPlan:
    """Produce the executable edit plan for one render."""
    if not report.ok:
        raise CreativeError(
            "input inspection found blocking problems: " + "; ".join(report.blocking_problems)
        )

    artists = [
        str((job.tracks.get("first") or {}).get("artist", "")),
        str((job.tracks.get("second") or {}).get("artist", "")),
    ]

    if format_override:
        templates = load_templates()
        if format_override not in templates:
            raise CreativeError(
                f"unknown format {format_override!r}; available: {sorted(templates)}"
            )
        template = templates[format_override]
        choice = FormatChoice(
            name=format_override,
            family=str(template.get("family", format_override)),
            template=template,
            score=1.0,
            reasons=["format forced by revision feedback"],
            rejected=[],
        )
        resolved = prefs.resolve(format_family=choice.family, artists=artists)
    else:
        resolved = prefs.resolve(artists=artists)
        choice = choose_format(job, report, resolved)
        resolved = prefs.resolve(format_family=choice.family, artists=artists)

    template = choice.template
    config = job.config
    timing = plan_timing(job, report, template)
    placement = _spotify_placement(template, resolved)
    protected = protected_regions_for(report.crop_profile, {
        "x": placement.x, "y": placement.y,
        "width": placement.width, "height": placement.height,
    })

    hook_text, hook_rationale = choose_hook(job, report, template)
    cta_text, cta_rationale = choose_cta(job, template)

    secondary, secondary_warnings = _plan_secondary(
        job, report, template, timing, resolved, protected
    )
    cues, text_warnings = _build_text_cues(
        job, template, timing, hook_text, cta_text, protected, resolved,
        secondary=secondary,
    )

    emphasis_cfg = config["transition"]["emphasis"]
    emphasis_enabled = bool(emphasis_cfg.get("enabled", True))
    if "zoom_emphasis" in resolved.banned_devices:
        emphasis_enabled = False
    if resolved.get("zoom_emphasis") is False:
        emphasis_enabled = False
    emphasis = Emphasis(
        enabled=emphasis_enabled,
        at_seconds=round(timing.transition_output, 3),
        amount=float(emphasis_cfg.get("zoom_amount", 0.08)),
        attack_seconds=float(emphasis_cfg.get("zoom_attack_seconds", 0.35)),
        release_seconds=float(emphasis_cfg.get("zoom_release_seconds", 0.55)),
    )

    bar_cfg = dict(config["progress_bar"])
    if "progress_bar" in resolved.banned_devices or resolved.get("progress_bar") is False:
        bar_cfg["enabled"] = False

    loudness = report.loudness or {}
    audio_cfg = config["audio"]
    audio = AudioPlan(
        source_path=str(job.spotify_recording),
        normalise=bool(audio_cfg["loudness_normalise"]) and bool(
            loudness.get("needs_normalisation", False)
        ),
        target_lufs=float(audio_cfg["loudness_target_lufs"]),
        true_peak_db=float(audio_cfg["loudness_true_peak_db"]),
        measured_lufs=loudness.get("integrated_lufs"),
        reason=str(loudness.get("reason", "no loudness measurement available")),
    )

    experiment = None
    if config["experiment"]["auto_attach"]:
        experiment = ExperimentPlan(
            hypothesis=str(template.get("retention_hypothesis", "")).strip()
            or f"The {choice.family} format holds attention through the transition.",
            variable="format_family",
            control_reference="clean_showcase",
            expected_effect="higher_completion_rate",
        )

    plan = EditPlan(
        job_id=job.job_id,
        revision=revision,
        format_family=choice.family,
        template_name=choice.name,
        source_in_seconds=timing.source_in,
        source_out_seconds=timing.source_out,
        duration_seconds=timing.duration,
        transition_output_seconds=timing.transition_output,
        transition_window=timing.transition_window,
        layout_mode=str((template.get("layout") or {}).get("mode", "full")),
        spotify_placement=placement,
        background="blurred_spotify",
        spotify_content_zoom=float(config["layout"].get("spotify_content_zoom", 0.0)),
        waveform_end_trim=float(config["layout"].get("waveform_end_trim", 0.0)),
        secondary_clips=secondary,
        text_cues=cues,
        emphasis=emphasis,
        progress_bar=bar_cfg,
        audio=audio,
        hook_text=hook_text,
        cta_text=cta_text,
        retention_hypothesis=str(template.get("retention_hypothesis", "")).strip(),
        research_refs=list(research_refs or []),
        preference_refs=resolved.refs(),
        warnings=[*timing.notes, *secondary_warnings, *text_warnings],
        experiment=experiment,
    )

    plan.creative_rationale = [
        f"format {choice.name}: " + "; ".join(choice.reasons),
        hook_rationale,
        cta_rationale,
    ]
    plan.add_decision(
        f"format_family={choice.family}",
        "; ".join(choice.reasons),
    )
    plan.add_decision(
        f"source window {timing.source_in:.2f}s-{timing.source_out:.2f}s",
        f"keeps the transition at {timing.transition_output:.2f}s of a "
        f"{timing.duration:.2f}s edit, with the cut clear of the blend region",
        stage="retention",
    )
    if emphasis.enabled:
        plan.add_decision(
            f"zoom emphasis at {emphasis.at_seconds:.2f}s",
            "marks the payoff visually without altering the audio",
            stage="retention",
        )
    for clip in secondary:
        plan.add_decision(
            f"{clip.mode} clip {clip.label!r} {clip.start_seconds:.2f}-{clip.end_seconds:.2f}s",
            clip.rationale,
            stage="retention",
        )
    for entry in choice.rejected:
        plan.add_decision(
            f"rejected format {entry['format']}", entry["reason"], stage="creative"
        )

    return plan
