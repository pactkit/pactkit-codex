"""Tests for STORY-slim-006: _render_prompt() and prompt placeholder replacement.

Covers:
- AC1: Zero ~/.claude/skills/ remaining in prompt source files
- AC2: Classic deployment renders actual paths (no {VAR} remnants)
- AC3: OpenCode deployment renders opencode paths (no ~/.claude/ remnants)
- AC4: JSON braces in templates are not replaced
- AC5: PROJECT_CONFIG path correct per format
- AC6: profiles.py docstring contains Template Variable Reference
- AC7: Full regression (covered by existing test suite, verified separately)
"""

import re
from pathlib import Path

import pytest

_PROJECT_ROOT = Path(__file__).parent.parent.parent  # repo root

PROMPT_SOURCE_FILES = [
    _PROJECT_ROOT / "src/pactkit/prompts/skills.py",
    _PROJECT_ROOT / "src/pactkit/prompts/commands.py",
    _PROJECT_ROOT / "src/pactkit/prompts/workflows.py",
    _PROJECT_ROOT / "src/pactkit/prompts/agents.py",
]


class TestAC1NoHardcodedSkillsPath:
    """AC1: ~/.claude/skills/ must not appear in prompt source files.

    Tests the SOURCE FILE content (not the in-memory module which may be mutated by other tests).
    """

    @pytest.mark.parametrize("filepath", PROMPT_SOURCE_FILES)
    def test_no_classic_skills_path(self, filepath):
        content = Path(filepath).read_text(encoding="utf-8")
        matches = [line.strip() for line in content.splitlines() if "~/.claude/skills/" in line]
        assert not matches, f"{filepath} still contains hardcoded '~/.claude/skills/':\n" + "\n".join(matches[:5])

    @pytest.mark.parametrize("filepath", PROMPT_SOURCE_FILES)
    def test_no_opencode_skills_path(self, filepath):
        content = Path(filepath).read_text(encoding="utf-8")
        matches = [line.strip() for line in content.splitlines() if "~/.config/opencode/skills/" in line]
        assert not matches, f"{filepath} still contains hardcoded '~/.config/opencode/skills/':\n" + "\n".join(
            matches[:5]
        )


# ---------------------------------------------------------------------------
# AC2 & AC3: _render_prompt() renders correct paths per format
# ---------------------------------------------------------------------------


class TestRenderPrompt:
    """Test the _render_prompt() function."""

    def _get_render_prompt(self):
        from pactkit.generators.deployer import _render_prompt

        return _render_prompt

    def _get_profile(self, name):
        from pactkit.profiles import get_profile

        return get_profile(name)

    def test_classic_renders_claude_skills(self):
        """Classic: {SKILLS_ROOT} → ~/.claude/skills."""
        render = self._get_render_prompt()
        profile = self._get_profile("classic")
        result = render("python3 {SKILLS_ROOT}/pactkit-board/scripts/board.py", profile)
        assert "~/.claude/skills" in result
        assert "{SKILLS_ROOT}" not in result

    def test_opencode_renders_opencode_skills(self):
        """OpenCode: {SKILLS_ROOT} → ~/.config/opencode/skills."""
        render = self._get_render_prompt()
        profile = self._get_profile("opencode")
        result = render("python3 {SKILLS_ROOT}/pactkit-board/scripts/board.py", profile)
        assert "~/.config/opencode/skills" in result
        assert "{SKILLS_ROOT}" not in result

    def test_visualize_cmd_derived(self):
        """Derived variable {VISUALIZE_CMD} expands correctly."""
        render = self._get_render_prompt()
        profile = self._get_profile("classic")
        result = render("{VISUALIZE_CMD} visualize", profile)
        assert "~/.claude/skills/pactkit-visualize/scripts/visualize.py visualize" in result

    def test_board_cmd_derived(self):
        render = self._get_render_prompt()
        profile = self._get_profile("opencode")
        result = render("{BOARD_CMD} archive", profile)
        assert "~/.config/opencode/skills/pactkit-board/scripts/board.py archive" in result

    def test_scaffold_cmd_derived(self):
        render = self._get_render_prompt()
        profile = self._get_profile("opencode")
        result = render("{SCAFFOLD_CMD} create_spec", profile)
        assert "~/.config/opencode/skills/pactkit-scaffold/scripts/scaffold.py create_spec" in result

    def test_pactkit_yaml_classic(self):
        render = self._get_render_prompt()
        profile = self._get_profile("classic")
        result = render("Check {PACTKIT_YAML}", profile)
        assert ".claude/pactkit.yaml" in result

    def test_pactkit_yaml_opencode(self):
        """AC5: OpenCode format uses .opencode/pactkit.yaml."""
        render = self._get_render_prompt()
        profile = self._get_profile("opencode")
        result = render("Check {PACTKIT_YAML}", profile)
        assert ".opencode/pactkit.yaml" in result
        assert ".claude/pactkit.yaml" not in result

    def test_global_instructions_classic(self):
        render = self._get_render_prompt()
        profile = self._get_profile("classic")
        result = render("See {GLOBAL_INSTRUCTIONS}", profile)
        assert "~/.claude/CLAUDE.md" in result

    def test_global_instructions_opencode(self):
        render = self._get_render_prompt()
        profile = self._get_profile("opencode")
        result = render("See {GLOBAL_INSTRUCTIONS}", profile)
        assert "~/.config/opencode/AGENTS.md" in result

    def test_display_name(self):
        render = self._get_render_prompt()
        profile = self._get_profile("opencode")
        result = render("Using {DISPLAY_NAME}", profile)
        assert "OpenCode" in result

    def test_unknown_placeholder_does_not_raise(self):
        """Sequential replacement: unknown {VAR} keys are left as-is (no error)."""
        render = self._get_render_prompt()
        profile = self._get_profile("classic")
        # {STORY_ID} is a user-facing placeholder, not a profile variable
        result = render("Story {STORY_ID} in {SKILLS_ROOT}", profile)
        assert "{STORY_ID}" in result  # left unchanged
        assert "~/.claude/skills" in result

    def test_all_variables_resolved_for_all_formats(self):
        """All profile variables render without remnant placeholders."""
        render = self._get_render_prompt()
        template = (
            "{SKILLS_ROOT} {RULES_ROOT} {GLOBAL_CONFIG_DIR} {PROJECT_CONFIG_DIR} "
            "{INSTRUCTIONS_FILE} {PACTKIT_YAML} {DISPLAY_NAME} "
            "{VISUALIZE_CMD} {BOARD_CMD} {SCAFFOLD_CMD} {GLOBAL_INSTRUCTIONS}"
        )
        for fmt in ["classic", "opencode"]:
            from pactkit.profiles import get_profile

            profile = get_profile(fmt)
            result = render(template, profile)
            # No unreplaced placeholders from our known variable set
            unreplaced = re.findall(
                r"\{(SKILLS_ROOT|RULES_ROOT|GLOBAL_CONFIG_DIR|PROJECT_CONFIG_DIR|"
                r"INSTRUCTIONS_FILE|PACTKIT_YAML|DISPLAY_NAME|VISUALIZE_CMD|"
                r"BOARD_CMD|SCAFFOLD_CMD|GLOBAL_INSTRUCTIONS)\}",
                result,
            )
            assert not unreplaced, f"Unreplaced vars in {fmt}: {unreplaced}"


# ---------------------------------------------------------------------------
# AC4: JSON braces not replaced
# ---------------------------------------------------------------------------


class TestAC4JsonBraces:
    """AC4: Escaped {{ }} in templates produce literal { } in output."""

    def test_json_braces_not_replaced(self):
        from pactkit.generators.deployer import _render_prompt
        from pactkit.profiles import get_profile

        profile = get_profile("opencode")
        # With sequential replacement, JSON braces are naturally safe
        template = '{\n  "$schema": "https://opencode.ai/config.json"\n}'
        result = _render_prompt(template, profile)
        assert result == template  # unchanged — no known vars to replace

    def test_mixed_json_and_variables(self):
        from pactkit.generators.deployer import _render_prompt
        from pactkit.profiles import get_profile

        profile = get_profile("classic")
        # JSON braces are naturally safe with sequential replacement
        template = 'Run `{BOARD_CMD}` and check {"key": "value"}'
        result = _render_prompt(template, profile)
        assert "~/.claude/skills/pactkit-board/scripts/board.py" in result
        assert '{"key": "value"}' in result


# ---------------------------------------------------------------------------
# AC5: PROJECT_CONFIG in deployed prompts
# ---------------------------------------------------------------------------


class TestAC5ProjectConfigInPrompts:
    """AC5: Deployed prompts use correct project config path per format."""

    def test_commands_project_config_placeholder(self):
        """commands.py source uses {PACTKIT_YAML} not hardcoded paths."""
        content = (_PROJECT_ROOT / "src/pactkit/prompts/commands.py").read_text(encoding="utf-8")
        assert "{PACTKIT_YAML}" in content, (
            "commands.py should use {PACTKIT_YAML} placeholder for config path references"
        )


# ---------------------------------------------------------------------------
# AC6: profiles.py docstring contains Template Variable Reference
# ---------------------------------------------------------------------------


class TestAC6ProfilesDocstring:
    """AC6: FormatProfile docstring includes Template Variable Reference table."""

    def test_docstring_has_variable_reference(self):
        from pactkit.profiles import FormatProfile

        doc = FormatProfile.__doc__ or ""
        assert "Template Variable Reference" in doc, (
            "FormatProfile docstring must contain 'Template Variable Reference' table"
        )

    def test_docstring_lists_key_variables(self):
        from pactkit.profiles import FormatProfile

        doc = FormatProfile.__doc__ or ""
        for var in ["SKILLS_ROOT", "PACTKIT_YAML", "VISUALIZE_CMD", "BOARD_CMD"]:
            assert var in doc, f"FormatProfile docstring missing variable: {var}"

    def test_docstring_explains_adding_format(self):
        from pactkit.profiles import FormatProfile

        doc = FormatProfile.__doc__ or ""
        assert "Adding a new format" in doc or "new format" in doc.lower(), (
            "FormatProfile docstring should explain how to add a new format"
        )


# ---------------------------------------------------------------------------
# AC2 & AC3: Integration — no ~/.claude/ in deployed opencode files
# ---------------------------------------------------------------------------


class TestDeployedOutputIntegration:
    """Integration: verify deployed output has correct paths."""

    def test_classic_skill_md_has_classic_path(self, tmp_path):
        """After deploy, SKILL.md should have ~/.claude/skills/ paths."""
        from pactkit.config import VALID_SKILLS
        from pactkit.generators.deployer import _deploy_skills
        from pactkit.profiles import get_profile

        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()
        profile = get_profile("classic")
        _deploy_skills(skills_dir, sorted(VALID_SKILLS), profile=profile)

        visualize_skill = skills_dir / "pactkit-visualize" / "SKILL.md"
        assert visualize_skill.exists()
        content = visualize_skill.read_text()
        assert "~/.claude/skills" in content
        assert "{VISUALIZE_CMD}" not in content

    def test_opencode_skill_md_has_opencode_path(self, tmp_path):
        """After deploy, OpenCode SKILL.md should have ~/.config/opencode/skills/ paths."""
        from pactkit.config import VALID_SKILLS
        from pactkit.generators.deployer import _deploy_skills
        from pactkit.profiles import get_profile

        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()
        profile = get_profile("opencode")
        _deploy_skills(skills_dir, sorted(VALID_SKILLS), profile=profile)

        visualize_skill = skills_dir / "pactkit-visualize" / "SKILL.md"
        assert visualize_skill.exists()
        content = visualize_skill.read_text()
        assert "~/.config/opencode/skills" in content
        assert "~/.claude/skills" not in content
        assert "{VISUALIZE_CMD}" not in content

    def test_classic_command_has_classic_path(self, tmp_path):
        """Classic commands should have ~/.claude/skills/ references."""
        from pactkit.generators.deployer import _deploy_commands
        from pactkit.profiles import get_profile

        cmd_dir = tmp_path / "commands"
        cmd_dir.mkdir()
        profile = get_profile("classic")
        _deploy_commands(cmd_dir, ["project-done"], profile=profile)

        done_cmd = cmd_dir / "project-done.md"
        assert done_cmd.exists()
        content = done_cmd.read_text()
        assert "~/.claude/skills" in content
        assert "{BOARD_CMD}" not in content

    def test_opencode_command_no_claude_path(self, tmp_path):
        """OpenCode commands must not contain ~/.claude/ references."""
        from pactkit.generators.deployer import _deploy_commands
        from pactkit.profiles import get_profile

        cmd_dir = tmp_path / "commands"
        cmd_dir.mkdir()
        profile = get_profile("opencode")
        _deploy_commands(cmd_dir, ["project-done"], profile=profile)

        done_cmd = cmd_dir / "project-done.md"
        content = done_cmd.read_text()
        assert "~/.config/opencode/skills" in content
        assert "~/.claude/skills" not in content
        assert "{BOARD_CMD}" not in content
