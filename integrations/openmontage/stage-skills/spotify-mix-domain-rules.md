# Spotify mix domain rules (project-scoped)

Provider: essence-of-virality  
Version: 0.1.0  
Upstream pipeline: screen-demo @ 4eab34c5

These rules apply to every stage when producing TikTok edits from Spotify mix screen
recordings. They mirror the operational skills in this repository's skill bank.

## Non-negotiables

1. **Music is the product** — use `preserve-spotify-mix-audio` before any audio change.
   Never add trending Sounds, narration beds, or SFX over the mix.
2. **Honest hooks** — use `evaluate-hook-clarity`; no false controversy or register mismatch.
3. **Transition is the payoff** — use `evaluate-transition-payoff`; structural fixes only,
   never alter the blend audio.
4. **Spotify legibility** — UI must remain recognisable in frame; test at mobile size.
5. **First frame promise** — use `analyse-first-frame` before export.

## Skill references (authoritative sources in this repo)

| Skill | Bank | When |
|---|---|---|
| preserve-spotify-mix-audio | spotify-mix-content | Before any audio processing |
| evaluate-transition-payoff | spotify-mix-content | After edit plan, before compose |
| analyse-first-frame | general-virality | Before export |
| evaluate-hook-clarity | general-virality | Idea + assets stages |

## TikTok export contract

- Profile: `tiktok` (1080×1920, 30 fps, H.264/AAC)
- Duration: 10–40 s preferred
- Posting: manual only — `export_bundle` packages files; no autonomous publish
