"""Tests for BUG-005: No hardcoded .claude/.opencode paths in Codex-only codebase.

Note: TestAC1NoClaudeInSkillScripts, TestAC3CLIHelpText, and
TestAC5VisualizeWorkflowPaths were removed in the thin-adapter migration.
Skills scripts now come from pactkit core and are path-replaced during
deployment by CodexDeployer.deploy_codex_skills(). There is no local copy
of skills/ or cli.py in this package.
"""

from pathlib import Path

SRC_DIR = Path("src/pactkit_codex")


class TestAC2NoOpencode:
    """AC2: No .opencode paths anywhere in source."""

    def test_no_opencode_in_src(self):
        matches = []
        for py_file in SRC_DIR.rglob("*.py"):
            for i, line in enumerate(py_file.read_text().split("\n"), 1):
                if ".opencode" in line:
                    matches.append(f"{py_file}:{i}: {line.strip()}")
        assert matches == [], ".opencode refs found:\n" + "\n".join(matches)



