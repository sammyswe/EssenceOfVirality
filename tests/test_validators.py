"""Tests for the deterministic validators. The repo itself must always pass."""

import sys
import textwrap
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "tools"))

import check_ids
import lint_skills
import run_fixtures
import validate_artifacts
from common import iter_artifact_files


def test_repo_artifacts_validate():
    assert validate_artifacts.validate_repo() == []


def test_repo_ids_consistent():
    assert check_ids.check_repo() == []


def test_repo_skills_lint():
    assert lint_skills.lint_all() == []


def test_repo_fixtures_valid():
    assert run_fixtures.check_fixtures() == []


def test_repo_has_artifacts():
    assert len(list(iter_artifact_files())) > 0, "vertical slice artifacts should exist"


def test_invalid_artifact_rejected(tmp_path):
    bad = tmp_path / "research"
    bad.mkdir()
    (bad / "bad.yaml").write_text(
        textwrap.dedent(
            """\
            artifact_type: claim_record
            id: claim-test-bad
            created_at: 2026-08-03
            produced_by: test
            statement: too-short
            claim_type: not_a_type
            """
        ),
        encoding="utf-8",
    )
    errors = validate_artifacts.validate_repo(tmp_path)
    assert errors, "invalid claim must produce validation errors"


def test_dangling_reference_detected(tmp_path):
    d = tmp_path / "evidence" / "claims"
    d.mkdir(parents=True)
    (d / "c.yaml").write_text(
        textwrap.dedent(
            """\
            artifact_type: claim_record
            id: claim-test-ok
            created_at: 2026-08-03
            produced_by: test
            source_ids: [src-does-not-exist]
            """
        ),
        encoding="utf-8",
    )
    errors = check_ids.check_repo(tmp_path)
    assert any("dangling" in e for e in errors)


def test_bad_skill_rejected(tmp_path):
    skill = tmp_path / "general-virality" / "bad-skill"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text(
        textwrap.dedent(
            """\
            ---
            name: wrong-name
            description: A skill that promises too much.
            ---
            This will go viral, guaranteed.
            """
        ),
        encoding="utf-8",
    )
    errors = lint_skills.lint_all(tmp_path)
    joined = "\n".join(errors)
    assert "!= folder" in joined
    assert "banned phrase" in joined
    assert "metadata.version" in joined
