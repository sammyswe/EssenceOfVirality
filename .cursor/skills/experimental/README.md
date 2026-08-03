# experimental/

Research-generated candidate skills awaiting promotion (ADR 0005).

- **What belongs**: new skills produced by `/refine-skills-from-source` or the skill architect,
  always `maturity: experimental`.
- **What does not**: anything routed to production use; workflow entry points; hand-authored
  skills that already passed review (they may be placed directly in a bank by a creator-reviewed
  PR).
- **Who writes**: the skill architect, via PRs.
- **Validation**: same lint as every bank (`tools/lint_skills.py`).
- **Exit paths**: promotion to a domain bank (PR + critic pass + fixtures) or deletion in the
  rejecting PR with the reason recorded in the skill-change proposal.

Empty right now: the phase-one exemplar skills were placed directly in their banks by the
reviewed phase-one PR.
