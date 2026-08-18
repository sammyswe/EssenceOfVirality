# Education videos → scroll-stop hook skill

You drop TikTok / tutorial videos about making hooks and retaining viewers into
Dropbox. The agent analyses them (no TikTok scraping — you supply the files) and
updates the **scroll-stop** craft used whenever a new Higgsfield hook is briefed.

## Dropbox folder

`/spotify-mix-videos/education/hooks-incoming/`

Paste exports or phone screen recordings of the tutorials there. After pull they
move to `education/hooks-imported/`.

Create the tree anytime with:

```bash
./process-job dropbox ensure
```

## Loop

1. Paste videos into `education/hooks-incoming/`.
2. Tell the agent: pull education and refine scroll-stop craft.
3. The agent runs `./process-job dropbox pull-education` (files land under
   `tmp/education/hooks/` — **never committed**).
4. Each video is analysed into findings; transferable moves become entries in
   `.cursor/skills/experimental/produce-scroll-stop-hook/references/techniques.md`
   with `channel_fit` checked against this niche.
5. Future hook briefs use `produce-scroll-stop-hook`, which applies every
   *active* technique or records why it skipped one.

## Rules

- Source videos stay out of git (`SECURITY.md` / content handling).
- Techniques are hypotheses about viewer behaviour, never algorithm claims or
  virality guarantees.
- Channel-fit rejects ("mixes itself", fake third-party reactions) always win
  over a trendy tutorial tip.

## Related

- Skill: `.cursor/skills/experimental/produce-scroll-stop-hook/`
- Hook clip library: `/spotify-mix-videos/hooks/library/`
- Profiles: `production/config/hook-profiles/`
