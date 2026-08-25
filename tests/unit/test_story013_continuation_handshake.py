"""Codex adapter contract for PactKit workflow continuation."""

from pactkit.profiles import get_profile

from pactkit_codex.deployer import CodexDeployer


def test_codex_adapter_deploys_native_session_playbooks_and_reports_capability(tmp_path):
    codex_root = tmp_path / "codex"
    skills = codex_root / "skills"
    skills.mkdir(parents=True)
    CodexDeployer.deploy_codex_command_skills(skills, get_profile("codex"))
    for command in ("project-plan", "project-act"):
        content = (skills / command / "SKILL.md").read_text()
        assert "pactkit-codex-work-unit" not in content
        assert "--owner codex" not in content
        assert "pactkit workflow finish-guard" not in content
    assert "workflow/checkpoint records are optional historical context" in (
        skills / "project-plan" / "SKILL.md"
    ).read_text().lower()

    capability = CodexDeployer.continuation_capabilities(codex_root)
    assert capability["finish_guard_supported"] is False
    assert capability["auto_resume_available"] is False
    assert capability["guarantee_level"] == "portable"
    assert capability["execution_mode"] == "portable"
    assert capability["session_execution"] == "native_current_session"
    assert capability["stop_hook_required"] is False


def test_codex_deployed_core_rule_makes_context_optional(tmp_path):
    rules = tmp_path / "rules"
    CodexDeployer.deploy_codex_rules(rules, get_profile("codex"))

    content = (rules / "pactkit.md").read_text(encoding="utf-8").lower()
    assert "optional history" in content
    assert "current-session work" in content
