"""Tests for BUG-005: No hardcoded .claude/.opencode paths in Codex-only codebase."""

from pathlib import Path

SRC_DIR = Path("src/pactkit_codex")
SKILLS_DIR = SRC_DIR / "skills"


class TestAC1NoClaudeInSkillScripts:
    """AC1: No runtime .claude paths in skill scripts."""

    def test_visualize_no_claude(self):
        content = (SKILLS_DIR / "visualize.py").read_text()
        # Filter out comments that legitimately reference the upstream project
        lines = [
            line for line in content.split("\n")
            if ".claude" in line and not line.strip().startswith("#")
        ]
        assert lines == [], f"Runtime .claude refs in visualize.py: {lines}"

    def test_board_no_claude(self):
        content = (SKILLS_DIR / "board.py").read_text()
        lines = [
            line for line in content.split("\n")
            if ".claude" in line and not line.strip().startswith("#")
        ]
        assert lines == [], f"Runtime .claude refs in board.py: {lines}"

    def test_scaffold_no_claude(self):
        content = (SKILLS_DIR / "scaffold.py").read_text()
        lines = [
            line for line in content.split("\n")
            if ".claude" in line and not line.strip().startswith("#")
        ]
        assert lines == [], f"Runtime .claude refs in scaffold.py: {lines}"


class TestAC2NoOpencode:
    """AC2: No .opencode paths anywhere in source."""

    def test_no_opencode_in_src(self):
        matches = []
        for py_file in SRC_DIR.rglob("*.py"):
            for i, line in enumerate(py_file.read_text().split("\n"), 1):
                if ".opencode" in line:
                    matches.append(f"{py_file}:{i}: {line.strip()}")
        assert matches == [], ".opencode refs found:\n" + "\n".join(matches)


class TestAC3CLIHelpText:
    """AC3: CLI help text references ~/.codex, not ~/.claude."""

    def test_cli_help_no_claude(self):
        content = (SRC_DIR / "cli.py").read_text()
        lines = [
            line for line in content.split("\n")
            if ".claude" in line
        ]
        assert lines == [], f".claude refs in cli.py: {lines}"


class TestAC5VisualizeWorkflowPaths:
    """AC5: visualize.py workflow staleness checks use .codex paths."""

    def test_workflow_staleness_uses_codex_dirs(self):
        content = (SKILLS_DIR / "visualize.py").read_text()
        # The workflow staleness check should reference .codex directories
        assert ".codex/prompts" in content or ".codex/skills" in content
        assert ".claude/commands" not in content

    def test_list_rules_references_codex(self):
        content = (SKILLS_DIR / "visualize.py").read_text()
        assert "~/.claude/CLAUDE.md" not in content

    def test_pdca_markers_use_codex(self):
        content = (SKILLS_DIR / "visualize.py").read_text()
        # PDCA detection markers should use .codex paths
        assert "'.codex/prompts/'" in content or '".codex/prompts/"' in content
        assert "'.claude/commands/'" not in content and '".claude/commands/"' not in content
