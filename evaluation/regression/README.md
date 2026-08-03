# evaluation/regression/

Before/after records for skill changes (ADR 0005, spec regression rule).

- **What belongs**: one subdirectory per skill change
  (`<skill-name>-v<old>-to-v<new>/`) containing the old and new outputs against the same
  fixtures, a prose diff of material differences, and the critic's
  improvements-and-regressions verdict as an `evaluation_report` YAML.
- **What does not**: ad-hoc experiments (use `tmp/`), reports unrelated to a skill version bump
  (use `../reports/`).
- **Who writes**: the evaluation agent, during `/evaluate-skill` and
  `/refine-skills-from-source`.
- **Validation**: YAML artifacts here are schema-validated by CI.
- Source-controlled: yes — regression history is part of the audit trail.

Empty until the first skill version bump; the directory exists because the workflows write here.
