"""
STORY-073: OpenCode Format Final Mile — Command Model Routing and Claude Code Residuals
Tests for command model routing (in opencode.json), project-init conditional, YAML comments, doc strings.
"""

import json

from pactkit.config import get_default_config
from pactkit.generators.deployer import deploy

try:
    from pactkit.generators.deployer import _resolve_opencode_model_id
except ImportError:
    _resolve_opencode_model_id = None


# ===========================================================================
# AC1: OpenCode model routing is in opencode.json command section
# ===========================================================================


class TestAC1CommandModel:
    """AC1: Model routing is in opencode.json command section (not frontmatter)."""

    def _deploy_with_providers(self, tmp_path):
        """Deploy with seeded provider config so model resolution works in CI."""
        out = tmp_path / "oc"
        out.mkdir(parents=True, exist_ok=True)
        providers = {
            "$schema": "https://opencode.ai/config.json",
            "provider": {
                "test-provider": {
                    "models": {
                        "claude-sonnet-4.6": {"name": "Sonnet"},
                        "claude-opus-4.6": {"name": "Opus"},
                        "claude-haiku-4.5": {"name": "Haiku"},
                    }
                }
            },
        }
        (out / "opencode.json").write_text(json.dumps(providers))
        deploy(format="opencode", target=str(out))
        return out

    def test_act_model_in_opencode_json(self, tmp_path):
        """project-act model routing is in opencode.json command section."""
        out = self._deploy_with_providers(tmp_path)
        data = json.loads((out / "opencode.json").read_text())
        cmd_config = data.get("command", {})
        assert "project-act" in cmd_config
        assert "model" in cmd_config["project-act"]
        assert "sonnet" in cmd_config["project-act"]["model"]

    def test_done_model_in_opencode_json(self, tmp_path):
        """project-done model routing is in opencode.json command section."""
        out = self._deploy_with_providers(tmp_path)
        data = json.loads((out / "opencode.json").read_text())
        assert "project-done" in data.get("command", {})

    def test_check_model_in_opencode_json(self, tmp_path):
        """project-check model routing is in opencode.json command section."""
        out = self._deploy_with_providers(tmp_path)
        data = json.loads((out / "opencode.json").read_text())
        assert "project-check" in data.get("command", {})

    def test_frontmatter_has_no_model(self, tmp_path):
        """Command frontmatter should NOT contain model: (routing is in opencode.json)."""
        out = self._deploy_with_providers(tmp_path)
        content = (out / "commands" / "project-act.md").read_text()
        parts = content.split("---", 2)
        frontmatter = parts[1]
        for line in frontmatter.strip().split("\n"):
            assert not line.strip().startswith("model:"), f"Unexpected model in frontmatter: {line}"


# ===========================================================================
# AC2: Plan command NOT in command routing
# ===========================================================================


class TestAC2PlanNoModel:
    """AC2: Commands that inherit main model are NOT in opencode.json command section."""

    def test_plan_not_in_command_routing(self, tmp_path):
        """project-plan is NOT in opencode.json command section."""
        out = tmp_path / "oc"
        out.mkdir(parents=True, exist_ok=True)
        providers = {"$schema": "x", "provider": {"tp": {"models": {"claude-sonnet-4.6": {}}}}}
        (out / "opencode.json").write_text(json.dumps(providers))
        deploy(format="opencode", target=str(out))
        data = json.loads((out / "opencode.json").read_text())
        assert "project-plan" not in data.get("command", {})

    def test_clarify_not_in_command_routing(self, tmp_path):
        """project-clarify is NOT in opencode.json command section."""
        out = tmp_path / "oc"
        out.mkdir(parents=True, exist_ok=True)
        providers = {"$schema": "x", "provider": {"tp": {"models": {"claude-sonnet-4.6": {}}}}}
        (out / "opencode.json").write_text(json.dumps(providers))
        deploy(format="opencode", target=str(out))
        data = json.loads((out / "opencode.json").read_text())
        assert "project-clarify" not in data.get("command", {})


# ===========================================================================
# AC3: Classic format has no model field
# ===========================================================================


class TestAC3ClassicNoModel:
    """AC3: Classic format commands never have model: field."""

    def test_classic_no_model(self, tmp_path):
        """Classic project-act.md has no model: field."""
        out = tmp_path / "classic"
        deploy(format="classic", target=str(out))
        content = (out / "commands" / "project-act.md").read_text()
        parts = content.split("---", 2)
        frontmatter = parts[1]
        for line in frontmatter.strip().split("\n"):
            assert not line.strip().startswith("model:"), f"Unexpected model: {line}"


# ===========================================================================
# AC4: project-init conditional (playbook text check)
# ===========================================================================


class TestAC4InitConditional:
    """AC4: project-init has conditional CLAUDE.md vs AGENTS.md."""

    def test_init_has_conditional(self):
        """project-init playbook has OpenCode conditional for CLAUDE.md."""
        from pactkit.prompts import COMMANDS_CONTENT

        init_content = COMMANDS_CONTENT["project-init.md"]
        assert "OpenCode" in init_content
        assert "AGENTS.md" in init_content
        assert "Claude Code" in init_content or ".claude/" in init_content


# ===========================================================================
# AC5: YAML comments have no ~/.claude/
# ===========================================================================


class TestAC5YamlComments:
    """AC5: Generated pactkit.yaml comments don't reference ~/.claude/."""

    def test_default_yaml_no_claude_path(self):
        """generate_default_yaml() output has no ~/.claude/ in comments."""
        from pactkit.config import generate_default_yaml

        yaml_text = generate_default_yaml()
        for line in yaml_text.split("\n"):
            if line.strip().startswith("#"):
                assert "~/.claude/" not in line, f"Comment references ~/.claude/: {line}"

    def test_rewrite_yaml_no_claude_path(self, tmp_path, monkeypatch):
        """_rewrite_yaml() output has no ~/.claude/ in comments."""
        from pactkit.config import _rewrite_yaml

        monkeypatch.chdir(tmp_path)
        yaml_path = tmp_path / "test.yaml"
        _rewrite_yaml(yaml_path, get_default_config())
        content = yaml_path.read_text()
        for line in content.split("\n"):
            if line.strip().startswith("#"):
                assert "~/.claude/" not in line, f"Comment references ~/.claude/: {line}"


# ===========================================================================
# AC6: User can override command model + resolver tests
# ===========================================================================


class TestAC6CommandModelOverride:
    """AC6: command_models in config and model resolver."""

    def test_default_config_has_command_models(self):
        """Default config includes command_models."""
        defaults = get_default_config()
        assert "command_models" in defaults
        assert isinstance(defaults["command_models"], dict)

    def test_resolve_model_id_sonnet(self):
        """_resolve_opencode_model_id resolves 'sonnet' to provider model ID."""
        providers = {
            "my-provider": {
                "models": {
                    "claude-sonnet-4.6": {"name": "Sonnet"},
                    "claude-opus-4.6": {"name": "Opus"},
                }
            }
        }
        result = _resolve_opencode_model_id("sonnet", providers)
        assert result == "my-provider/claude-sonnet-4.6"

    def test_resolve_model_id_haiku(self):
        """_resolve_opencode_model_id resolves 'haiku' to provider model ID."""
        providers = {"my-provider": {"models": {"claude-haiku-4.5": {"name": "Haiku"}}}}
        result = _resolve_opencode_model_id("haiku", providers)
        assert result == "my-provider/claude-haiku-4.5"

    def test_resolve_model_id_not_found(self):
        """_resolve_opencode_model_id returns None when model not found."""
        providers = {"my-provider": {"models": {"gpt-4": {"name": "GPT"}}}}
        result = _resolve_opencode_model_id("sonnet", providers)
        assert result is None

    def test_resolve_model_id_empty_providers(self):
        """_resolve_opencode_model_id returns None with empty providers."""
        result = _resolve_opencode_model_id("sonnet", {})
        assert result is None


# ===========================================================================
# R4: Skills.py doc string update
# ===========================================================================


class TestR4DocStrings:
    """R4: skills.py doc strings mention both paths."""

    def test_skills_mention_opencode_path(self):
        """Skill doc strings use {SKILLS_ROOT} template variable (STORY-slim-006).
        The actual path is injected at deploy time via _render_prompt()."""
        from pactkit.prompts import skills as skills_mod

        full_text = ""
        for attr_name in dir(skills_mod):
            val = getattr(skills_mod, attr_name)
            if isinstance(val, str) and "Script location" in val:
                full_text += val
        if full_text:
            # After STORY-slim-006, skills use {BOARD_CMD}/{VISUALIZE_CMD}/{SCAFFOLD_CMD} placeholders
            has_placeholder = (
                "{BOARD_CMD}" in full_text or "{VISUALIZE_CMD}" in full_text or "{SCAFFOLD_CMD}" in full_text
            )
            assert has_placeholder, "Skill SKILL.md should use {BOARD_CMD}/{VISUALIZE_CMD}/{SCAFFOLD_CMD} placeholders"
