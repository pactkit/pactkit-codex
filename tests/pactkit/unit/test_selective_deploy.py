"""
STORY-002: Selective Deployment — Deployer filters by pactkit.yaml config.
"""

from pathlib import Path
from unittest.mock import patch

from pactkit.config import get_default_config
from pactkit.generators.deployer import deploy
from pactkit.prompts import AGENTS_EXPERT, COMMANDS_CONTENT, RULES_FILES

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _run_deploy(tmp_path, config=None):
    """Run deploy() with ~/.claude and $CWD redirected to tmp_path (BUG-013)."""
    claude_root = tmp_path / ".claude"
    for d in [claude_root, claude_root / "agents", claude_root / "commands", claude_root / "skills"]:
        d.mkdir(parents=True, exist_ok=True)

    with (
        patch.object(Path, "home", return_value=tmp_path),
        patch("pactkit.generators.deployer.Path.cwd", return_value=tmp_path),
    ):
        deploy(config=config)

    return claude_root


# ===========================================================================
# S1: Full config deploys everything
# ===========================================================================


class TestFullConfigDeploysAll:
    def test_all_agents_deployed(self, tmp_path):
        claude = _run_deploy(tmp_path, config=get_default_config())
        agents_dir = claude / "agents"
        for name in AGENTS_EXPERT:
            assert (agents_dir / f"{name}.md").is_file(), f"Missing agent: {name}"

    def test_all_commands_deployed(self, tmp_path):
        claude = _run_deploy(tmp_path, config=get_default_config())
        cmds_dir = claude / "commands"
        for filename in COMMANDS_CONTENT:
            assert (cmds_dir / filename).is_file(), f"Missing command: {filename}"

    def test_all_skills_deployed(self, tmp_path):
        claude = _run_deploy(tmp_path, config=get_default_config())
        skills_dir = claude / "skills"
        for skill_name in ["pactkit-visualize", "pactkit-board", "pactkit-scaffold"]:
            assert (skills_dir / skill_name / "SKILL.md").is_file(), f"Missing skill: {skill_name}"

    def test_all_rules_deployed(self, tmp_path):
        claude = _run_deploy(tmp_path, config=get_default_config())
        rules_dir = claude / "rules"
        for filename in RULES_FILES.values():
            assert (rules_dir / filename).is_file(), f"Missing rule: {filename}"

    def test_no_config_means_full_deploy(self, tmp_path):
        """Backward compat: deploy() with no config deploys everything."""
        claude = _run_deploy(tmp_path, config=None)
        agents_dir = claude / "agents"
        for name in AGENTS_EXPERT:
            assert (agents_dir / f"{name}.md").is_file()


# ===========================================================================
# S2: Partial agent config
# ===========================================================================


class TestPartialAgentConfig:
    def test_only_selected_agents_deployed(self, tmp_path):
        cfg = get_default_config()
        cfg["agents"] = ["system-architect", "senior-developer"]

        claude = _run_deploy(tmp_path, config=cfg)
        agents_dir = claude / "agents"

        assert (agents_dir / "system-architect.md").is_file()
        assert (agents_dir / "senior-developer.md").is_file()

        # Others should NOT exist
        assert not (agents_dir / "qa-engineer.md").exists()
        assert not (agents_dir / "repo-maintainer.md").exists()
        assert not (agents_dir / "security-auditor.md").exists()

    def test_stale_agents_cleaned_on_partial(self, tmp_path):
        """Pre-existing managed agents not in config should be removed."""
        claude = tmp_path / ".claude"
        agents_dir = claude / "agents"
        agents_dir.mkdir(parents=True)
        # Seed a managed agent that won't be in partial config
        (agents_dir / "qa-engineer.md").write_text("stale")

        cfg = get_default_config()
        cfg["agents"] = ["system-architect"]
        _run_deploy(tmp_path, config=cfg)

        assert not (agents_dir / "qa-engineer.md").exists()

    def test_user_custom_agent_preserved(self, tmp_path):
        claude = tmp_path / ".claude"
        agents_dir = claude / "agents"
        agents_dir.mkdir(parents=True)
        (agents_dir / "my-custom-agent.md").write_text("user content")

        cfg = get_default_config()
        cfg["agents"] = ["system-architect"]
        _run_deploy(tmp_path, config=cfg)

        assert (agents_dir / "my-custom-agent.md").is_file()
        assert (agents_dir / "my-custom-agent.md").read_text() == "user content"


# ===========================================================================
# S3: Partial command config
# ===========================================================================


class TestPartialCommandConfig:
    def test_only_selected_commands_deployed(self, tmp_path):
        cfg = get_default_config()
        cfg["commands"] = ["project-plan", "project-act", "project-done"]

        claude = _run_deploy(tmp_path, config=cfg)
        cmds_dir = claude / "commands"

        assert (cmds_dir / "project-plan.md").is_file()
        assert (cmds_dir / "project-act.md").is_file()
        assert (cmds_dir / "project-done.md").is_file()

        # Others should NOT exist
        assert not (cmds_dir / "project-check.md").exists()
        assert not (cmds_dir / "project-sprint.md").exists()

    def test_user_custom_command_preserved(self, tmp_path):
        claude = tmp_path / ".claude"
        cmds_dir = claude / "commands"
        cmds_dir.mkdir(parents=True)
        (cmds_dir / "ultra-think.md").write_text("user command")

        cfg = get_default_config()
        cfg["commands"] = ["project-plan"]
        _run_deploy(tmp_path, config=cfg)

        assert (cmds_dir / "ultra-think.md").is_file()


# ===========================================================================
# S4: CLAUDE.md reflects enabled rules only
# ===========================================================================


class TestSelectiveRules:
    def test_claude_md_no_global_rule_imports(self, tmp_path):
        """STORY-slim-011: CLAUDE.md no longer has rule @imports (moved to per-command)."""
        cfg = get_default_config()
        cfg["rules"] = ["01-core-protocol", "05-workflow-conventions"]

        claude = _run_deploy(tmp_path, config=cfg)
        content = (claude / "CLAUDE.md").read_text()

        # STORY-slim-011: CLAUDE.md should have no rule filenames at all
        assert "01-core-protocol.md" not in content
        assert "05-workflow-conventions.md" not in content
        assert "@./docs/product/context.md" in content

    def test_only_enabled_rule_files_exist(self, tmp_path):
        cfg = get_default_config()
        cfg["rules"] = ["01-core-protocol"]

        claude = _run_deploy(tmp_path, config=cfg)
        rules_dir = claude / "rules"

        assert (rules_dir / "01-core-protocol.md").is_file()
        assert not (rules_dir / "02-hierarchy-of-truth.md").exists()
        assert not (rules_dir / "06-mcp-integration.md").exists()

    def test_full_rules_deploys_all(self, tmp_path):
        cfg = get_default_config()
        claude = _run_deploy(tmp_path, config=cfg)
        rules_dir = claude / "rules"

        for filename in RULES_FILES.values():
            assert (rules_dir / filename).is_file()


# ===========================================================================
# S5: Idempotent re-deploy preserves user config
# ===========================================================================


class TestIdempotentDeploy:
    def test_existing_yaml_not_overwritten(self, tmp_path):
        claude = tmp_path / ".claude"
        claude.mkdir(parents=True)
        yaml_path = claude / "pactkit.yaml"
        original_content = 'agents:\n  - system-architect\nversion: "9.9.9"\n'
        yaml_path.write_text(original_content)

        _run_deploy(tmp_path, config=get_default_config())

        assert yaml_path.read_text() == original_content


# ===========================================================================
# S6: Config file auto-generated on first init
# ===========================================================================


class TestConfigAutoGeneration:
    def test_yaml_created_when_missing(self, tmp_path):
        claude = _run_deploy(tmp_path, config=get_default_config())
        yaml_path = claude / "pactkit.yaml"
        assert yaml_path.is_file()

    def test_generated_yaml_is_valid(self, tmp_path):
        import yaml

        claude = _run_deploy(tmp_path, config=get_default_config())
        yaml_path = claude / "pactkit.yaml"
        parsed = yaml.safe_load(yaml_path.read_text())
        assert parsed is not None
        assert "agents" in parsed


# ===========================================================================
# S7: Deployment summary is printed
# ===========================================================================


class TestDeploymentSummary:
    def test_summary_printed_full(self, tmp_path, capsys):
        # STORY-051: 11 commands (added project-release, project-pr)
        _run_deploy(tmp_path, config=get_default_config())
        output = capsys.readouterr().out
        assert "9/9 Agents" in output
        assert "11/11 Commands" in output
        assert "10/10 Skills" in output
        assert "8/8 Rules" in output or "9/9 Rules" in output  # 9 rules after 09-sectional-write

    def test_summary_printed_partial(self, tmp_path, capsys):
        # STORY-051: total commands is now 11
        cfg = get_default_config()
        cfg["agents"] = ["system-architect", "senior-developer"]
        cfg["commands"] = ["project-plan", "project-act", "project-done"]

        _run_deploy(tmp_path, config=cfg)
        output = capsys.readouterr().out
        assert "2/9 Agents" in output
        assert "3/11 Commands" in output


# ===========================================================================
# S8: Custom target directory works (via deploy with target param)
# ===========================================================================


class TestCustomTarget:
    def test_deploy_with_target(self, tmp_path):
        target = tmp_path / "custom-target"
        with patch("pactkit.generators.deployer.Path.cwd", return_value=tmp_path):
            deploy(config=get_default_config(), target=str(target))

        assert (target / "agents").is_dir()
        assert (target / "commands").is_dir()
        assert (target / "skills").is_dir()
        assert (target / "CLAUDE.md").is_file()
        # Config is generated at $CWD/.claude/, not at target (BUG-013)
        assert (tmp_path / ".claude" / "pactkit.yaml").is_file()

    def test_target_agents_deployed(self, tmp_path):
        target = tmp_path / "custom-target"
        deploy(config=get_default_config(), target=str(target))

        for name in AGENTS_EXPERT:
            assert (target / "agents" / f"{name}.md").is_file()


# ===========================================================================
# Selective skill deployment
# ===========================================================================


class TestSelectiveSkills:
    def test_only_selected_skills_deployed(self, tmp_path):
        cfg = get_default_config()
        cfg["skills"] = ["pactkit-visualize"]

        claude = _run_deploy(tmp_path, config=cfg)
        skills_dir = claude / "skills"

        assert (skills_dir / "pactkit-visualize" / "SKILL.md").is_file()
        assert not (skills_dir / "pactkit-board" / "SKILL.md").exists()
        assert not (skills_dir / "pactkit-scaffold" / "SKILL.md").exists()

    def test_empty_skills_deploys_none(self, tmp_path):
        cfg = get_default_config()
        cfg["skills"] = []

        claude = _run_deploy(tmp_path, config=cfg)
        skills_dir = claude / "skills"

        for name in ["pactkit-visualize", "pactkit-board", "pactkit-scaffold"]:
            assert not (skills_dir / name / "SKILL.md").exists()
