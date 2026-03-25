"""Tests for BUG-001: Playbook script paths use ~ (shell built-in) instead of $HOME (env var)."""

import re


def _prompts():
    import importlib

    import pactkit.prompts as p

    importlib.reload(p)
    return p


# ==============================================================================
# Scenario 1: No $HOME References Remain
# ==============================================================================
class TestNoHomeVarReferences:
    """BUG-001: No $HOME/.claude/skills/ references — use ~ instead."""

    def test_no_dollar_home_in_commands(self):
        """No COMMANDS_CONTENT value should contain $HOME/.claude/skills/."""
        p = _prompts()
        for name, content in p.COMMANDS_CONTENT.items():
            assert "$HOME/.claude/skills/" not in content, f"{name} still contains $HOME/.claude/skills/"

    def test_no_dollar_home_in_trace_prompt(self):
        """TRACE_PROMPT should not contain $HOME/.claude/skills/."""
        p = _prompts()
        assert "$HOME/.claude/skills/" not in p.TRACE_PROMPT


# ==============================================================================
# Scenario 2: All Invocations Use Tilde (~) Pattern
# ==============================================================================
class TestTildePattern:
    """BUG-001: All skill invocations use ~/.claude/skills/ (shell built-in)."""

    def test_visualize_calls_use_tilde(self):
        """All visualize.py invocations should use ~/ or $SKILLS_PATH (environment-aware)."""
        p = _prompts()
        for name, content in p.COMMANDS_CONTENT.items():
            if "visualize.py" in content:
                assert "~/.claude/skills/" in content or "$SKILLS_PATH" in content, (
                    f"{name} references visualize.py without ~/ prefix or $SKILLS_PATH variable"
                )

    def test_board_calls_use_tilde(self):
        """All board.py invocations should use ~/ or $SKILLS_PATH (environment-aware)."""
        p = _prompts()
        for name, content in p.COMMANDS_CONTENT.items():
            if "board.py" in content:
                assert "~/.claude/skills/" in content or "$SKILLS_PATH" in content, (
                    f"{name} references board.py without ~/ prefix or $SKILLS_PATH variable"
                )

    def test_trace_uses_tilde(self):
        """TRACE_PROMPT visualize.py invocation should use ~/."""
        p = _prompts()
        if "visualize.py" in p.TRACE_PROMPT:
            assert "~/.claude/skills/" in p.TRACE_PROMPT


# ==============================================================================
# Scenario 3: No runpy Overhead
# ==============================================================================
class TestNoRunpyOverhead:
    """BUG-001: No runpy.run_path pattern in playbooks (unnecessary complexity)."""

    def test_no_runpy_in_commands(self):
        p = _prompts()
        for name, content in p.COMMANDS_CONTENT.items():
            assert "runpy.run_path" not in content, f"{name} still uses runpy.run_path"

    def test_no_runpy_in_trace(self):
        p = _prompts()
        assert "runpy.run_path" not in p.TRACE_PROMPT


# ==============================================================================
# Scenario 4: Correct Script Paths
# ==============================================================================
class TestCorrectPaths:
    """BUG-001: All ~/.claude/skills/ paths reference valid skill scripts."""

    def test_valid_skill_paths(self):
        p = _prompts()
        all_content = "\n".join(p.COMMANDS_CONTENT.values()) + "\n" + p.TRACE_PROMPT
        for m in re.finditer(r'~/.claude/skills/([^\s`"]+\.py)', all_content):
            path = m.group(0)
            assert (
                "pactkit-visualize/scripts/visualize.py" in path
                or "pactkit-board/scripts/board.py" in path
                or "pactkit-scaffold/scripts/scaffold.py" in path
            ), f"Unknown skill path: {path}"


# ==============================================================================
# Scenario 5: Backward Compatibility
# ==============================================================================
class TestBackwardCompatibility:
    """BUG-001: All existing commands and agents still present."""

    def test_existing_commands_present(self):
        p = _prompts()
        expected = [
            "project-plan.md",
            "project-act.md",
            "project-check.md",
            "project-done.md",
            "project-init.md",
            "project-sprint.md",
            "project-hotfix.md",
            "project-design.md",
        ]
        for cmd in expected:
            assert cmd in p.COMMANDS_CONTENT, f"Missing {cmd}"

    def test_agents_unchanged(self):
        p = _prompts()
        expected_agents = [
            "system-architect",
            "senior-developer",
            "qa-engineer",
            "repo-maintainer",
            "system-medic",
            "security-auditor",
            "visual-architect",
            "code-explorer",
        ]
        for agent in expected_agents:
            assert agent in p.AGENTS_EXPERT, f"Missing agent {agent}"

    def test_lang_profiles_preserved(self):
        p = _prompts()
        for lang in ["python", "node", "go", "java"]:
            assert lang in p.LANG_PROFILES
            assert "test_runner" in p.LANG_PROFILES[lang]
