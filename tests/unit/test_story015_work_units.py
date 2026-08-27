import json
from pathlib import Path

try:
    import tomllib
except ImportError:  # Python 3.10
    import tomli as tomllib

import pytest

from pactkit.profiles import get_profile

from pactkit_codex.deployer import CodexDeployer


def _tree_snapshot(root):
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }


def test_default_deploy_has_no_workflow_runner_methods_or_stop_hook(tmp_path):
    CodexDeployer().deploy(target=tmp_path)
    for name in (
        "pactkit-method-clarify", "pactkit-method-architecture-trace",
        "pactkit-method-spec-writing", "pactkit-method-tdd",
        "pactkit-method-verification", "pactkit-method-release-preparation",
    ):
        assert not (tmp_path / "skills" / name).exists()
    assert not (tmp_path / "hooks" / "pactkit_stop.py").exists()
    manifest = json.loads((tmp_path / ".pactkit-deployed.json").read_text())
    capability = manifest["workflow_continuation"]
    assert capability["execution_mode"] == "portable"
    assert capability["session_execution"] == "native_current_session"
    assert capability["stop_hook_required"] is False
    assert capability["auto_resume_available"] is False
    assert manifest["host_capabilities"]["thread_resume"] is False
    assert manifest["host_capabilities"]["session_execution"] == "native_current_session"


def test_upgrade_removes_only_unmodified_legacy_portable_method(tmp_path):
    from pactkit.generators.deployer import _render_skill_md
    from pactkit.portable_methods import get_portable_methods

    profile = get_profile("codex")
    method = get_portable_methods()[0]
    old = tmp_path / "skills" / method["name"] / "SKILL.md"
    old.parent.mkdir(parents=True)
    old.write_text(
        _render_skill_md(method, profile, profile.skills_path_var), encoding="utf-8",
    )
    user = tmp_path / "skills" / get_portable_methods()[1]["name"] / "SKILL.md"
    user.parent.mkdir(parents=True)
    user.write_text("custom method\n", encoding="utf-8")

    CodexDeployer().deploy(target=tmp_path)

    assert not old.parent.exists()
    assert user.read_text(encoding="utf-8") == "custom method\n"


def test_distribution_does_not_publish_the_experimental_runner():
    project = Path(__file__).resolve().parents[2]
    metadata = tomllib.loads((project / "pyproject.toml").read_text(encoding="utf-8"))

    assert "pactkit-codex-work-unit" not in metadata["project"].get("scripts", {})
    assert not (project / "src/pactkit_codex/runner.py").exists()
    assert not (project / "src/pactkit_codex/work_unit_adapter.py").exists()
    assert not (project / "src/pactkit_codex/app_server.py").exists()
    assert not (project / "src/pactkit_codex/stop_hook.py").exists()


def test_deploy_removes_only_the_legacy_pactkit_stop_hook(tmp_path):
    hooks = tmp_path / "hooks.json"
    hooks.write_text(
        json.dumps({
            "hooks": {
                "Stop": [
                    {"hooks": [{"type": "command", "command": "user-stop"}]},
                    {"hooks": [{"type": "command", "command": "pactkit-codex-stop-hook"}]},
                ],
            },
        }),
        encoding="utf-8",
    )

    CodexDeployer().deploy(target=tmp_path)

    payload = json.loads(hooks.read_text(encoding="utf-8"))
    commands = [item["hooks"][0]["command"] for item in payload["hooks"]["Stop"]]
    assert commands == ["user-stop"]


def test_legacy_stop_hook_migration_preserves_mixed_entries_and_custom_launcher(tmp_path):
    hooks = tmp_path / "hooks.json"
    hooks.write_text(
        json.dumps({
            "hooks": {
                "Stop": [{"hooks": [
                    {"type": "command", "command": "pactkit-codex-stop-hook"},
                    {"type": "command", "command": "user-stop"},
                ]}],
            },
        }),
        encoding="utf-8",
    )
    launcher = tmp_path / "hooks" / "pactkit_stop.py"
    launcher.parent.mkdir()
    launcher.write_text("# user customization\n", encoding="utf-8")

    CodexDeployer().deploy(target=tmp_path)

    payload = json.loads(hooks.read_text(encoding="utf-8"))
    handlers = payload["hooks"]["Stop"][0]["hooks"]
    assert handlers == [{"type": "command", "command": "user-stop"}]
    assert launcher.read_text(encoding="utf-8") == "# user customization\n"


def test_legacy_stop_hook_migration_removes_only_exact_legacy_launcher(tmp_path):
    from pactkit_codex.deployer import _LEGACY_STOP_LAUNCHER

    launcher = tmp_path / "hooks" / "pactkit_stop.py"
    launcher.parent.mkdir()
    launcher.write_text(_LEGACY_STOP_LAUNCHER, encoding="utf-8")

    CodexDeployer().deploy(target=tmp_path)

    assert not launcher.exists()


def test_legacy_stop_hook_migration_does_not_rewrite_unrelated_hooks(tmp_path):
    hooks = tmp_path / "hooks.json"
    original = '{  "hooks" : { "Stop" : [{"hooks":[{"command":"user-stop"}]}] } }'
    hooks.write_text(original, encoding="utf-8")

    CodexDeployer().deploy(target=tmp_path)

    assert hooks.read_text(encoding="utf-8") == original


def test_default_codex_manifest_uses_core_capability_level(tmp_path):
    CodexDeployer().deploy(target=tmp_path)

    manifest = json.loads((tmp_path / ".pactkit-deployed.json").read_text(encoding="utf-8"))
    assert manifest["host_capabilities"]["execution_mode"] == "portable"
    assert manifest["workflow_continuation"]["guarantee_level"] == "portable"
    assert manifest["workflow_continuation"]["session_execution"] == "native_current_session"
    host = manifest["host_capabilities"]
    assert host["verification_source"] == "native_codex_session"
    assert host["tool_execution"] is False
    assert host["lifecycle_events"] is False
    assert host["thread_resume"] is False
    assert host["background_execution"] is False


def test_project_plan_is_a_native_current_session_playbook(tmp_path):
    CodexDeployer.deploy_codex_command_skills(tmp_path, get_profile("codex"))
    plan = (tmp_path / "project-plan" / "SKILL.md").read_text()
    assert "Phase 0.7" in plan
    assert "workflow/checkpoint records are optional historical context" in plan.lower()
    assert "pactkit-codex-work-unit" not in plan
    assert "WorkUnit" not in plan


def test_every_project_command_is_deployed_as_native_current_session_playbook(tmp_path):
    from pactkit.config import VALID_COMMANDS

    CodexDeployer.deploy_codex_command_skills(tmp_path, get_profile("codex"))
    for command in VALID_COMMANDS:
        content = (tmp_path / command / "SKILL.md").read_text()
        assert "pactkit-codex-work-unit" not in content, command
        assert "--owner codex" not in content, command
        assert "Managed WorkUnit Facade" not in content, command
        assert "EvidenceReceipt" not in content, command


def test_canonical_classic_and_deployed_codex_act_have_equal_operations(tmp_path):
    """R5: compare canonical Classic Act with the actual Codex artifact."""
    import re

    from pactkit.generators.deploy_base import _REQUIRED_ACT_MARKERS
    from pactkit.generators.deployer import _render_prompt
    from pactkit.prompts.commands import COMMANDS_CONTENT

    classic = _render_prompt(COMMANDS_CONTENT["project-act.md"], get_profile("classic"))
    CodexDeployer.deploy_codex_command_skills(
        tmp_path, get_profile("codex"), enabled_commands=["project-act"],
    )
    codex = (tmp_path / "project-act" / "SKILL.md").read_text(encoding="utf-8")

    def normalized_operations(content):
        return set(re.findall(r"<!--\s*PACTKIT_ACT_OP:([a-z_]+)\s*-->", content))

    assert normalized_operations(classic) == set(_REQUIRED_ACT_MARKERS)
    assert normalized_operations(codex) == normalized_operations(classic)
    assert "~/.claude/" not in codex
    assert "`/project-act" not in codex
    assert "`$project-act" in codex


@pytest.mark.parametrize("payload", ["{not json", "[]", "null", '"hooks"', "1"])
def test_invalid_legacy_hooks_do_not_leave_deployment_half_finished(tmp_path, payload):
    hooks = tmp_path / "hooks.json"
    hooks.write_text(payload, encoding="utf-8")

    CodexDeployer().deploy(target=tmp_path)

    assert hooks.read_text(encoding="utf-8") == payload
    assert (tmp_path / ".pactkit-version").is_file()
    assert (tmp_path / ".pactkit-deployed.json").is_file()


def test_codex_sprint_is_a_real_current_session_fallback(tmp_path):
    CodexDeployer.deploy_codex_command_skills(tmp_path, get_profile("codex"))
    sprint = (tmp_path / "project-sprint" / "SKILL.md").read_text()

    assert "Sequential PDCA in the current Codex session" in sprint
    for phase in ("plan", "act", "check", "done"):
        assert f"references/phases/{phase}.md" in sprint
    for unavailable_api in ("TeamCreate", "TaskCreate", "SendMessage", "TeamDelete"):
        assert unavailable_api not in sprint
    assert "commands/project-" not in sprint


def test_codex_command_selection_removes_only_owned_disabled_command(tmp_path):
    deployer = CodexDeployer()
    deployer.deploy(
        target=tmp_path, config={"commands": ["project-act", "project-plan"]},
    )
    skills = tmp_path / "skills"
    assert (skills / "project-act" / "references" / "guides" / "caching.md").is_file()

    deployer.deploy(target=tmp_path, config={"commands": ["project-plan"]})

    assert (skills / "project-plan" / "SKILL.md").is_file()
    assert not (skills / "project-act").exists()


def test_failed_command_selection_keeps_old_command_and_manifest(tmp_path, monkeypatch):
    """A render failure must not remove a command from the previous deploy."""
    import pactkit_codex.deployer as deployer_module

    profile = get_profile("codex")
    CodexDeployer.deploy_codex_command_skills(
        tmp_path, profile, enabled_commands=["project-act"],
    )
    old_command = tmp_path / "project-act" / "SKILL.md"
    manifest = tmp_path / ".pactkit-command-manifest.json"
    old_manifest = manifest.read_bytes()
    original = deployer_module._enforce_deploy_integrity

    def fail_command(content, current_profile, label):
        if label == "command_skill:project-plan":
            raise RuntimeError("forced render failure")
        return original(content, current_profile, label)

    monkeypatch.setattr(deployer_module, "_enforce_deploy_integrity", fail_command)
    with pytest.raises(RuntimeError, match="forced render failure"):
        CodexDeployer.deploy_codex_command_skills(
            tmp_path, profile, enabled_commands=["project-plan"],
        )

    assert old_command.is_file()
    assert manifest.read_bytes() == old_manifest


def test_failed_command_write_keeps_old_disabled_command(tmp_path, monkeypatch):
    """A storage failure must leave the prior selection usable."""
    import pactkit_codex.deployer as deployer_module

    profile = get_profile("codex")
    CodexDeployer.deploy_codex_command_skills(
        tmp_path, profile, enabled_commands=["project-act"],
    )
    old_command = tmp_path / "project-act" / "SKILL.md"
    manifest = tmp_path / ".pactkit-command-manifest.json"
    old_manifest = manifest.read_bytes()
    original = deployer_module.atomic_write

    def fail_new_command(path, content):
        if path == tmp_path / "project-plan" / "SKILL.md":
            raise OSError("forced command write failure")
        return original(path, content)

    monkeypatch.setattr(deployer_module, "atomic_write", fail_new_command)
    with pytest.raises(OSError, match="forced command write failure"):
        CodexDeployer.deploy_codex_command_skills(
            tmp_path, profile, enabled_commands=["project-plan"],
        )

    assert old_command.is_file()
    assert manifest.read_bytes() == old_manifest


def test_later_command_write_failure_rolls_back_earlier_new_command(tmp_path, monkeypatch):
    """A multi-command write is all-or-restore before deselection cleanup."""
    import pactkit_codex.deployer as deployer_module

    profile = get_profile("codex")
    CodexDeployer.deploy_codex_command_skills(
        tmp_path, profile, enabled_commands=["project-act"],
    )
    old_command = tmp_path / "project-act" / "SKILL.md"
    manifest = tmp_path / ".pactkit-command-manifest.json"
    old_manifest = manifest.read_bytes()
    original = deployer_module.atomic_write

    def fail_second_new_command(path, content):
        if path == tmp_path / "project-plan" / "SKILL.md":
            raise OSError("forced later command write failure")
        return original(path, content)

    monkeypatch.setattr(deployer_module, "atomic_write", fail_second_new_command)
    with pytest.raises(OSError, match="forced later command write failure"):
        CodexDeployer.deploy_codex_command_skills(
            tmp_path, profile, enabled_commands=["project-init", "project-plan"],
        )

    assert old_command.is_file()
    assert not (tmp_path / "project-init" / "SKILL.md").exists()
    assert manifest.read_bytes() == old_manifest


def test_failed_full_deploy_preflight_keeps_previous_install(tmp_path, monkeypatch):
    """A later generated artifact failure must not partially update Codex."""
    deployer = CodexDeployer()
    initial = {"skills": [], "commands": ["project-act"]}
    deployer.deploy(target=tmp_path, config=initial)
    old_command = tmp_path / "skills" / "project-act" / "SKILL.md"
    old_content = old_command.read_text(encoding="utf-8")
    manifest = tmp_path / "skills" / ".pactkit-command-manifest.json"
    old_manifest = manifest.read_bytes()

    def fail_rules(*_args, **_kwargs):
        raise RuntimeError("forced rule render failure")

    monkeypatch.setattr(deployer, "deploy_codex_rules", fail_rules)
    with pytest.raises(RuntimeError, match="forced rule render failure"):
        deployer.deploy(
            target=tmp_path, config={"skills": [], "commands": ["project-plan"]},
        )

    assert old_command.read_text(encoding="utf-8") == old_content
    assert not (tmp_path / "skills" / "project-plan").exists()
    assert manifest.read_bytes() == old_manifest


def test_failure_after_live_writes_restores_entire_previous_deployment(
    tmp_path, monkeypatch,
):
    """A final manifest failure must roll back every managed live write."""
    deployer = CodexDeployer()
    deployer.deploy(
        target=tmp_path,
        config={"skills": ["pactkit-board"], "commands": ["project-act"]},
    )
    before = _tree_snapshot(tmp_path)

    def fail_manifest(*_args, **_kwargs):
        user_file = tmp_path / "skills" / "pactkit-board" / "notes.md"
        user_file.parent.mkdir(parents=True, exist_ok=True)
        user_file.write_text("concurrent user content\n", encoding="utf-8")
        raise OSError("forced final manifest failure")

    monkeypatch.setattr(deployer, "_write_deployment_manifest", fail_manifest)
    with pytest.raises(OSError, match="forced final manifest failure"):
        deployer.deploy(
            target=tmp_path,
            config={"skills": [], "commands": ["project-plan"]},
        )

    after = _tree_snapshot(tmp_path)
    user_path = "skills/pactkit-board/notes.md"
    assert after.pop(user_path) == b"concurrent user content\n"
    assert after == before


def test_selective_deploy_keeps_codex_runtime_free_of_command_catalogs(tmp_path):
    CodexDeployer().deploy(
        target=tmp_path, config={"commands": ["project-plan"]},
    )

    agents = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
    rules = (tmp_path / "rules" / "pactkit-runtime.md").read_text(encoding="utf-8")
    assert "project-plan" not in agents
    assert "/project-" not in agents
    for disabled in ("project-act", "project-check", "project-done", "project-sprint"):
        assert f"${disabled}" not in agents
        assert f"${disabled}" not in rules

    for rule in (tmp_path / "rules").rglob("*.md"):
        content = rule.read_text(encoding="utf-8")
        for disabled in ("project-act", "project-check", "project-done", "project-sprint"):
            assert f"${disabled}" not in content, rule.name
        assert f"/{disabled}" not in content, rule.name
