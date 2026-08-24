"""Codex adapter contract for PactKit workflow continuation."""

from pactkit.profiles import get_profile

from pactkit_codex.deployer import CodexDeployer


def test_codex_adapter_preserves_pre_final_protocol_and_reports_real_capability(tmp_path):
    codex_root = tmp_path / "codex"
    skills = codex_root / "skills"
    skills.mkdir(parents=True)
    CodexDeployer.deploy_codex_command_skills(skills, get_profile("codex"))
    for command in ("project-plan", "project-act"):
        content = (skills / command / "SKILL.md").read_text()
        assert "Pre-Final Protocol" in content
        assert "finish-guard" in content
        assert "continue_current_turn" in content
        assert "await_user" in content
        assert "Progress is not final" in content

    capability = CodexDeployer.continuation_capabilities(codex_root)
    assert capability["finish_guard_supported"] is True
    assert capability["auto_resume_available"] is False
    assert capability["guarantee_level"] == "resumable"
    assert capability["execution_mode"] == "resumable"
    assert capability["stop_hook_required"] is False
