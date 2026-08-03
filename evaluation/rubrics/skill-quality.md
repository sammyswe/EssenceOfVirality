# Rubric: Skill Quality

Applied by the skill critic to every `skill_change_proposal`. Each dimension is rated
weak / adequate / strong with a one-line justification. No aggregate score — a skill weak on any
gate dimension (marked ⛔) requires revision regardless of other strengths.

| # | Dimension | Gate | What strong looks like |
|---|---|---|---|
| 1 | Trigger specificity | ⛔ | Invocation and non-invocation conditions are concrete; a reader can decide "fires / doesn't fire" for ten scenarios without guessing |
| 2 | Input definition | ⛔ | Required and optional inputs named with formats; preconditions checkable |
| 3 | Actionability of steps | ⛔ | Each step is an action with a completion criterion; no step is "consider..." without a decision rule |
| 4 | Testable output contract | ⛔ | Output shape stated (fields/format); a fixture can assert against it |
| 5 | Prohibitions explicit | | Anti-patterns and must-not behaviours listed and paired with what to do instead |
| 6 | Behaviour linkage | ⛔ | Every technique states its intended viewer behaviour/metric target; no claims of direct algorithmic effect |
| 7 | Epistemic honesty | ⛔ | No certainty beyond evidence; confidence/maturity metadata consistent with `evidence_refs` |
| 8 | Scope discipline | | One concern; background material disclosed into references, not inlined |
| 9 | Example quality | | At least one worked example and one counterexample that would genuinely mislead a naive skill |
| 10 | Niche fit | | For domain skills: respects music-centrality, Spotify legibility, anonymous format |
| 11 | Duplication | ⛔ | No overlap with an existing skill's decision rights; composes rather than restates |
| 12 | No-op language | | No sentences the executing agent would follow identically if deleted |

Critic verdict: `passed` / `revisions_required` (with the failing dimensions listed). Two
revision rounds maximum before escalation to the creator.
