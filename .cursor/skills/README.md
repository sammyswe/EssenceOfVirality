# .cursor/skills/ — project skill banks

Project-authored Agent Skills, auto-discovered by Cursor. Bank layout (ADR 0005, lint:
`tools/lint_skills.py`):

| Bank | Contents | Invocation style |
|---|---|---|
| `research-workflows/` | User-invoked workflow entry points (`/ingest-source`, ...) | `disable-model-invocation: true` |
| `meta/` | Skill authoring standard + research helper skills | model-invoked |
| `general-virality/` | Domain skills: platform-agnostic virality production rules | model-invoked, evidence-referenced |
| `spotify-mix-content/` | Domain skills: niche rules (music centrality, Spotify legibility) | model-invoked, evidence-referenced |
| `experimental/` | New research-generated candidates awaiting promotion | not routed to production use |
| `production/` | Operating instructions for the ten stages of `production/` | model-invoked |

`production/` skills describe how to run and reason about the video pipeline —
what each stage owns, its hard rules, its output contract and its failure modes.
They carry no `evidence_refs` because the creative claims they act on belong to
the domain banks; a production skill that starts asserting a domain finding
should link to the domain skill instead.

Third-party skills live in `.agents/skills/` (lockfile-managed) — never here.

Every skill carries `metadata`: `version` (semver), `maturity`
(experimental→provisional→validated→stable / deprecated), `confidence` (low/medium/high),
`evidence_basis`, `requires_human_approval`; domain banks also require `evidence_refs` (claim/
technique IDs). Lifecycle and promotion rules: ADR 0005 and `.cursor/rules/skills.mdc`.
