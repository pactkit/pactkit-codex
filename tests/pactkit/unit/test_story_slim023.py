"""Tests for STORY-slim-023: Auto Version Sync via pactkit update --if-needed."""

import subprocess

from pactkit import __version__
from pactkit.prompts.rules import RULES_MODULES


class TestR1IfNeededFlag:
    """R1: pactkit update MUST accept --if-needed flag."""

    def test_flag_accepted(self):
        """--if-needed does not raise argparse error."""
        result = subprocess.run(
            ["pactkit", "update", "--if-needed", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "--if-needed" in result.stdout

    def test_flag_in_help(self):
        """--if-needed appears in update help text."""
        result = subprocess.run(
            ["pactkit", "update", "--help"],
            capture_output=True,
            text=True,
        )
        assert "--if-needed" in result.stdout
        assert "redeploy" in result.stdout.lower() or "version" in result.stdout.lower()


class TestR2VersionComparison:
    """R2: CLI MUST read pactkit.yaml version and compare to __version__."""

    def test_reads_pactkit_yaml(self, tmp_path, monkeypatch):
        """When --if-needed is set, pactkit.yaml is read."""
        # Create pactkit.yaml with matching version
        yaml_dir = tmp_path / ".claude"
        yaml_dir.mkdir()
        yaml_file = yaml_dir / "pactkit.yaml"
        yaml_file.write_text(f'version: "{__version__}"\nstack: python\n')

        monkeypatch.chdir(tmp_path)
        result = subprocess.run(
            ["pactkit", "update", "--if-needed"],
            capture_output=True,
            text=True,
        )
        # Should skip (up-to-date) because versions match
        assert "up-to-date" in result.stdout or result.returncode == 0


class TestR3SkipOnMatch:
    """R3: If versions match, CLI MUST skip deploy."""

    def test_skip_message_when_match(self, tmp_path, monkeypatch):
        """Prints skip message when versions match."""
        yaml_dir = tmp_path / ".claude"
        yaml_dir.mkdir()
        yaml_file = yaml_dir / "pactkit.yaml"
        yaml_file.write_text(f'version: "{__version__}"\nstack: python\n')

        monkeypatch.chdir(tmp_path)
        result = subprocess.run(
            ["pactkit", "update", "--if-needed"],
            capture_output=True,
            text=True,
        )
        assert "up-to-date" in result.stdout
        assert "skipping" in result.stdout.lower()


class TestR4ProceedOnMismatch:
    """R4: If versions differ or no pactkit.yaml, CLI MUST proceed."""

    def test_proceed_when_mismatch(self, tmp_path, monkeypatch):
        """Proceeds with deploy when versions differ."""
        yaml_dir = tmp_path / ".claude"
        yaml_dir.mkdir()
        yaml_file = yaml_dir / "pactkit.yaml"
        yaml_file.write_text('version: "0.0.0"\nstack: python\n')

        monkeypatch.chdir(tmp_path)
        result = subprocess.run(
            ["pactkit", "update", "--if-needed"],
            capture_output=True,
            text=True,
        )
        # Should show mismatch message and proceed
        assert "mismatch" in result.stdout.lower() or "updating" in result.stdout.lower()

    def test_proceed_when_no_yaml(self, tmp_path, monkeypatch):
        """Proceeds with deploy when no pactkit.yaml exists."""
        monkeypatch.chdir(tmp_path)
        result = subprocess.run(
            ["pactkit", "update", "--if-needed"],
            capture_output=True,
            text=True,
        )
        # Should show first-time setup message
        assert "first-time" in result.stdout.lower() or "setup" in result.stdout.lower()


class TestR5CoreProtocolPrompt:
    """R5: Core Protocol prompt MUST include pactkit update --if-needed."""

    def test_core_protocol_contains_if_needed(self):
        """Session Context section references --if-needed."""
        core = RULES_MODULES["core"]
        assert "pactkit update --if-needed" in core

    def test_session_context_section_updated(self):
        """Session Context has version sync instruction."""
        core = RULES_MODULES["core"]
        assert "Session Context" in core
        # Version sync comes before reading context.md
        session_start = core.find("## Session Context")
        context_md = core.find("context.md", session_start)
        if_needed = core.find("--if-needed", session_start)
        assert if_needed < context_md, "Version sync should come before reading context.md"


class TestR6BlastRadius:
    """R6: Only cli.py and prompts/rules.py are modified."""

    def test_no_other_prompts_reference_if_needed(self):
        """No other RULES_MODULES reference --if-needed."""
        for name, content in RULES_MODULES.items():
            if name == "core":
                continue
            assert "--if-needed" not in content, f"Unexpected --if-needed in {name}"
