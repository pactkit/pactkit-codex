import json

from pactkit.profiles import get_profile

from pactkit_codex.deployer import CodexDeployer


def test_default_deploy_has_portable_methods_and_no_pactkit_stop_hook(tmp_path):
    CodexDeployer().deploy(target=tmp_path)
    for name in (
        "pactkit-method-clarify", "pactkit-method-architecture-trace",
        "pactkit-method-spec-writing", "pactkit-method-tdd",
        "pactkit-method-verification", "pactkit-method-release-preparation",
    ):
        assert (tmp_path / "skills" / name / "SKILL.md").is_file()
    assert not (tmp_path / "hooks" / "pactkit_stop.py").exists()
    manifest = json.loads((tmp_path / ".pactkit-deployed.json").read_text())
    capability = manifest["workflow_continuation"]
    assert capability["execution_mode"] == "resumable"
    assert capability["stop_hook_required"] is False
    assert capability["auto_resume_available"] is False


def test_project_plan_is_thin_work_unit_facade(tmp_path):
    CodexDeployer.deploy_codex_command_skills(tmp_path, get_profile("codex"))
    plan = (tmp_path / "project-plan" / "SKILL.md").read_text()
    assert "pactkit work-unit acquire" in plan
    assert "pactkit-codex-work-unit run" in plan
    assert "pactkit-codex-work-unit execute" not in plan
    assert "pactkit work-unit submit" in plan
    assert "managed runner is the sole finalizer" in plan
    assert "Portable/manual hosts only" in plan
    assert "Phase 0.7" not in plan


def test_every_project_command_is_deployed_as_managed_work_unit_facade(tmp_path):
    from pactkit.config import VALID_COMMANDS

    CodexDeployer.deploy_codex_command_skills(tmp_path, get_profile("codex"))
    for command in VALID_COMMANDS:
        content = (tmp_path / command / "SKILL.md").read_text()
        assert f"pactkit work-unit start {command}" in content
        assert "pactkit-codex-work-unit run <run-id> --owner codex" in content
        assert "Core" in content
    for command in ("project-act", "project-check", "project-done", "project-hotfix"):
        assert "--story-id <story-id>" in (tmp_path / command / "SKILL.md").read_text()
    for command in ("project-done", "project-pr", "project-release", "project-sprint"):
        assert "--authorize <operation>" in (tmp_path / command / "SKILL.md").read_text()
