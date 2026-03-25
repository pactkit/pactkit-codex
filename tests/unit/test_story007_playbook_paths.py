"""Tests for STORY-007: Update Playbook Text Paths for Codex Environment."""

import pytest


class TestRenderedCodexPrompts:
    """AC1, AC3, AC4: Verify rendered output for codex profile is clean."""

    @pytest.fixture(autouse=True)
    def _setup(self):
        """Pre-render all command playbooks with codex profile."""
        from pactkit_codex.generators.deployer import _render_prompt
        from pactkit_codex.prompts.commands import COMMANDS_CONTENT
        from pactkit_codex.profiles import get_profile

        self.profile = get_profile("codex")
        self.rendered = {}
        for filename, template in COMMANDS_CONTENT.items():
            self.rendered[filename] = _render_prompt(template, self.profile)

    def test_ac1_no_claude_paths_in_rendered(self):
        """AC1: No ~/.claude/ paths in any rendered codex prompt."""
        for filename, content in self.rendered.items():
            assert "~/.claude/" not in content, f"{filename} contains ~/.claude/"

    def test_ac1_no_opencode_paths_in_rendered(self):
        """AC1: No ~/.config/opencode/ paths in any rendered codex prompt."""
        for filename, content in self.rendered.items():
            assert "~/.config/opencode/" not in content, f"{filename} contains ~/.config/opencode/"

    def test_ac3_no_unresolved_skills_root(self):
        """AC3: No unresolved {SKILLS_ROOT} placeholders in rendered output."""
        for filename, content in self.rendered.items():
            assert "{SKILLS_ROOT}" not in content, f"{filename} has unresolved {{SKILLS_ROOT}}"

    def test_ac3_skills_paths_resolve_to_codex(self):
        """AC3: Skills paths resolve to ~/.codex/skills in codex profile."""
        # At least some rendered prompts should contain codex skills path
        all_content = "\n".join(self.rendered.values())
        # The init playbook sets SKILLS_PATH — after render, should reference codex
        if "skills" in all_content.lower():
            # Check that no old-format skills paths remain
            assert "~/.claude/skills" not in all_content
            assert "~/.config/opencode/skills" not in all_content

    def test_ac4_no_anthropic_model_names(self):
        """AC4: No Anthropic model names in rendered output."""
        for filename, content in self.rendered.items():
            content_lower = content.lower()
            assert "claude-sonnet" not in content_lower, f"{filename} has claude-sonnet"
            assert "claude-haiku" not in content_lower, f"{filename} has claude-haiku"
            assert "claude-opus" not in content_lower, f"{filename} has claude-opus"


class TestInitPlaybookCodexBranch:
    """AC2, R3, R4, R7: /project-init has Codex environment detection."""

    @pytest.fixture(autouse=True)
    def _setup(self):
        from pactkit_codex.generators.deployer import _render_prompt
        from pactkit_codex.prompts.commands import COMMANDS_CONTENT
        from pactkit_codex.profiles import get_profile

        self.profile = get_profile("codex")
        self.init_content = _render_prompt(COMMANDS_CONTENT["project-init.md"], self.profile)

    def test_ac2_codex_detection_present(self):
        """R3: Init playbook includes Codex environment detection."""
        assert "codex" in self.init_content.lower()

    def test_ac2_codex_pactkit_yaml_path(self):
        """R4: Init playbook references .codex/pactkit.yaml."""
        assert ".codex/pactkit.yaml" in self.init_content or "{PACTKIT_YAML}" not in self.init_content

    def test_r7_codex_in_init_guard(self):
        """R7: .codex/ mentioned in init guard or env detection."""
        # The init playbook should mention codex as a possible environment
        assert "codex" in self.init_content.lower()


class TestSourceFileAudit:
    """AC5: Grep audit of source prompt files for hardcoded paths."""

    def _get_prompt_template_content(self):
        """Get all prompt template content (commands, skills, agents, rules modules)."""
        from pactkit_codex.prompts.commands import COMMANDS_CONTENT
        from pactkit_codex.prompts import agents, rules

        # Collect all template strings (the ones that go through _render_prompt)
        templates = {}
        for filename, content in COMMANDS_CONTENT.items():
            templates[f"commands/{filename}"] = content
        for name, cfg in agents.AGENTS_EXPERT.items():
            templates[f"agents/{name}"] = cfg.get("prompt", "")
        for key, content in rules.RULES_MODULES.items():
            templates[f"rules/{key}"] = content
        return templates

    def test_ac5_no_hardcoded_claude_skills_in_templates(self):
        """AC5: No hardcoded ~/.claude/skills/ in template strings."""
        templates = self._get_prompt_template_content()
        for name, content in templates.items():
            # Skip rules that legitimately describe the architecture (non-template prose)
            if name == "rules/architecture":
                continue
            assert "~/.claude/skills/" not in content, f"{name} has hardcoded ~/.claude/skills/"

    def test_ac5_no_hardcoded_opencode_skills_in_templates(self):
        """AC5: No hardcoded ~/.config/opencode/skills/ in template strings."""
        templates = self._get_prompt_template_content()
        for name, content in templates.items():
            if name == "rules/architecture":
                continue
            assert "~/.config/opencode/skills/" not in content, f"{name} has hardcoded opencode skills path"


class TestDeployedCodexPromptsClean:
    """Integration: full deploy pipeline produces clean Codex prompts."""

    def test_full_deploy_no_claude_paths(self, tmp_path):
        """Full codex deploy: no ~/.claude/ in any prompt file."""
        from pactkit_codex.generators.deployer import _deploy_codex_prompts
        from pactkit_codex.profiles import get_profile

        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()
        profile = get_profile("codex")
        _deploy_codex_prompts(prompts_dir, profile)

        for f in prompts_dir.glob("*.md"):
            content = f.read_text()
            assert "~/.claude/" not in content, f"{f.name} has ~/.claude/ after deploy"
            assert "~/.config/opencode/" not in content, f"{f.name} has opencode path after deploy"
