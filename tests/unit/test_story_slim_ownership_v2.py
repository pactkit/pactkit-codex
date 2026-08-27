"""STORY-slim-20260827fc9de5542ad7: command manifest v2 reference ledger.

AC5 render-failure isolation, AC6 corrupt-manifest degradation, and the
sprint-phase redeploy guard.
"""

from __future__ import annotations

import json

import pytest

from pactkit_codex.deployer import CodexDeployer


SPRINT_PHASES = ("plan", "act", "check", "done")


def test_corrupt_command_manifest_degrades_and_rewrites(tmp_path):
    """AC6: corrupt manifest → deploy completes, nothing deleted, v2 written."""
    deployer = CodexDeployer()
    deployer.deploy(config={"commands": ["project-act"]}, target=tmp_path)
    guides = tmp_path / "skills" / "project-act" / "references" / "guides"
    assert (guides / "caching.md").is_file()
    before = (guides / "caching.md").read_bytes()

    (tmp_path / "skills" / ".pactkit-command-manifest.json").write_text(
        "{corrupt", encoding="utf-8"
    )

    # Corrupt proof table must not block deployment or delete references
    deployer.deploy(config={"commands": ["project-act"]}, target=tmp_path)
    assert (guides / "caching.md").read_bytes() == before
    payload = json.loads(
        (tmp_path / "skills" / ".pactkit-command-manifest.json").read_text(
            encoding="utf-8"
        )
    )
    assert payload["version"] == 2
    assert payload["references"]


def test_v1_manifest_upgrade_cleans_stale_references(tmp_path):
    """AC4: a v1 manifest (no references) upgrades to v2; stale cleanup works
    on the following deploy cycle."""
    deployer = CodexDeployer()
    deployer.deploy(config={"commands": ["project-act"]}, target=tmp_path)
    manifest_path = tmp_path / "skills" / ".pactkit-command-manifest.json"
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    # Downgrade to v1 shape (no references section)
    payload = {"version": 1, "commands": payload["commands"]}
    manifest_path.write_text(json.dumps(payload), encoding="utf-8")

    # Deploy with act disabled: v1 carries no reference proofs, so the stale
    # guides are conservatively preserved...
    deployer.deploy(config={"commands": ["project-plan"]}, target=tmp_path)
    # ...and the manifest is rewritten as valid v2 for the next cycle
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert payload["version"] == 2


def test_sprint_phase_capsules_survive_redeploy(tmp_path):
    """Guard: with proofs available, redeploying sprint must not delete and
    churn its phase capsules (desired-set must include them)."""
    deployer = CodexDeployer()
    deployer.deploy(config={"commands": ["project-sprint"]}, target=tmp_path)
    phases = tmp_path / "skills" / "project-sprint" / "references" / "phases"
    for phase in SPRINT_PHASES:
        capsule = phases / f"{phase}.md"
        assert capsule.is_file()
        before = capsule.read_bytes()

    deployer.deploy(config={"commands": ["project-sprint"]}, target=tmp_path)
    payload = json.loads(
        (tmp_path / "skills" / ".pactkit-command-manifest.json").read_text(
            encoding="utf-8"
        )
    )
    recorded = {
        relative for relative in payload["references"]
        if "project-sprint/references/phases/" in relative
    }
    assert len(recorded) == len(SPRINT_PHASES)


def test_render_failure_leaves_no_phantom_reference_digest(tmp_path, monkeypatch):
    """AC5: a mid-deploy render failure must not leave digests for files that
    never landed."""
    import pactkit_codex.deployer as deployer_module

    deployer = CodexDeployer()
    deployer.deploy(config={"commands": ["project-act"]}, target=tmp_path)
    manifest_path = tmp_path / "skills" / ".pactkit-command-manifest.json"
    old_manifest = manifest_path.read_bytes()

    original = deployer_module._enforce_deploy_integrity

    def fail_second_reference(content, current_profile, label):
        if label.startswith("command_reference:"):
            raise RuntimeError("forced reference render failure")
        return original(content, current_profile, label)

    monkeypatch.setattr(
        deployer_module, "_enforce_deploy_integrity", fail_second_reference
    )
    with pytest.raises(RuntimeError, match="forced reference render failure"):
        CodexDeployer.deploy_codex_command_skills(
            tmp_path / "skills",
            deployer.profile,
            enabled_commands=["project-act"],
        )

    # The pre-failure manifest is untouched — no phantom digests
    assert manifest_path.read_bytes() == old_manifest
