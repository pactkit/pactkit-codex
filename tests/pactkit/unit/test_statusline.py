"""Tests for STORY-029: Enhanced Claude Code StatusLine (Bash-native HUD).

Tests the bash statusLine command by piping mock JSON into it via subprocess
and verifying the output contains expected segments.
"""

import json
import re
import subprocess

import pytest

# The statusLine bash command under test.
# This will be populated after implementation — for now it's a placeholder.
STATUSLINE_CMD = ""


def _load_cmd() -> str:
    """Load the statusLine command from ~/.claude/settings.json."""
    import os
    import pathlib

    settings_path = pathlib.Path(os.path.expanduser("~/.claude/settings.json"))
    if not settings_path.exists():
        pytest.skip("~/.claude/settings.json not found")
    data = json.loads(settings_path.read_text())
    cmd = data.get("statusLine", {}).get("command", "")
    if not cmd:
        pytest.skip("statusLine.command not configured")
    return cmd


def _run_statusline(stdin_json: dict, cmd: str | None = None) -> str:
    """Pipe JSON into the statusLine command and return stdout (ANSI stripped)."""
    if cmd is None:
        cmd = _load_cmd()
    result = subprocess.run(
        ["bash", "-c", cmd],
        input=json.dumps(stdin_json),
        capture_output=True,
        text=True,
        timeout=5,
    )
    return result.stdout.strip()


def _strip_ansi(text: str) -> str:
    """Remove ANSI escape sequences for assertion matching."""
    return re.sub(r"\x1b\[[0-9;]*m", "", text)


def _make_stdin(
    model: str = "Opus",
    used_pct: int | None = 45,
    ctx_size: int = 200000,
    input_tokens: int = 45000,
    cache_create: int = 10000,
    cache_read: int = 30000,
    cwd: str = "/Users/test/workspaces/pactkit",
) -> dict:
    """Build a mock stdin JSON dict."""
    data: dict = {
        "model": {"display_name": model, "id": "claude-opus-4-test"},
        "context_window": {
            "context_window_size": ctx_size,
            "current_usage": {
                "input_tokens": input_tokens,
                "output_tokens": 5000,
                "cache_creation_input_tokens": cache_create,
                "cache_read_input_tokens": cache_read,
            },
        },
        "workspace": {"current_dir": cwd},
        "cwd": cwd,
    }
    if used_pct is not None:
        data["context_window"]["used_percentage"] = used_pct
        data["context_window"]["remaining_percentage"] = 100 - used_pct
    return data


# ---------------------------------------------------------------------------
# Scenario 1: Context Bar at Low Usage
# ---------------------------------------------------------------------------
class TestContextBar:
    def test_low_usage_shows_percentage(self):
        """R1: Bar with 30% shows '30%' and contains filled+empty blocks."""
        stdin = _make_stdin(used_pct=30)
        out = _strip_ansi(_run_statusline(stdin))
        assert "30%" in out
        # Bar should have 3 filled (█) and 7 empty (░) = 10 total
        assert "███" in out
        assert "░" in out

    def test_low_usage_no_token_count(self):
        """R2: Below 70%, no token count shown."""
        stdin = _make_stdin(used_pct=30)
        out = _strip_ansi(_run_statusline(stdin))
        # Should NOT contain parenthesized token count
        assert "k/" not in out


# ---------------------------------------------------------------------------
# Scenario 2: Token Count at High Usage
# ---------------------------------------------------------------------------
class TestTokenCount:
    def test_warning_shows_token_count(self):
        """R2: At 75%, shows percentage AND token count."""
        stdin = _make_stdin(
            used_pct=75,
            ctx_size=200000,
            input_tokens=100000,
            cache_create=30000,
            cache_read=20000,
        )
        out = _strip_ansi(_run_statusline(stdin))
        assert "75%" in out
        assert "150k" in out  # 100k+30k+20k = 150k tokens used
        assert "200k" in out  # context window size


# ---------------------------------------------------------------------------
# Scenario 3: Critical Warning
# ---------------------------------------------------------------------------
class TestCriticalWarning:
    def test_critical_shows_warning_icon(self):
        """R2: At 90%+, shows ⚠ warning indicator."""
        stdin = _make_stdin(
            used_pct=90,
            ctx_size=200000,
            input_tokens=150000,
            cache_create=20000,
            cache_read=10000,
        )
        out = _strip_ansi(_run_statusline(stdin))
        assert "90%" in out
        assert "⚠" in out

    def test_critical_shows_token_count(self):
        """R2: At 90%+, token count is still shown."""
        stdin = _make_stdin(
            used_pct=90,
            ctx_size=200000,
            input_tokens=150000,
            cache_create=20000,
            cache_read=10000,
        )
        out = _strip_ansi(_run_statusline(stdin))
        assert "180k" in out  # 150k+20k+10k
        assert "200k" in out


# ---------------------------------------------------------------------------
# Scenario 5: Model and Directory Preserved
# ---------------------------------------------------------------------------
class TestModelAndDirectory:
    def test_model_name_shown(self):
        """R5: Model name appears in brackets."""
        stdin = _make_stdin(model="Opus")
        out = _strip_ansi(_run_statusline(stdin))
        assert "[Opus]" in out

    def test_directory_shown(self):
        """R5: Directory name appears with folder icon."""
        stdin = _make_stdin(cwd="/Users/test/workspaces/myproject")
        out = _strip_ansi(_run_statusline(stdin))
        assert "myproject" in out


# ---------------------------------------------------------------------------
# Scenario 6: Graceful Fallback
# ---------------------------------------------------------------------------
class TestGracefulFallback:
    def test_malformed_json_produces_fallback(self):
        """R7: Malformed JSON produces fallback output, not error."""
        cmd = _load_cmd()
        result = subprocess.run(
            ["bash", "-c", cmd],
            input="NOT VALID JSON",
            capture_output=True,
            text=True,
            timeout=5,
        )
        out = _strip_ansi(result.stdout.strip())
        assert "[Claude Code]" in out or "[" in out  # some fallback shown
        assert result.returncode == 0

    def test_empty_stdin_produces_fallback(self):
        """R7: Empty stdin produces fallback output."""
        cmd = _load_cmd()
        result = subprocess.run(
            ["bash", "-c", cmd],
            input="",
            capture_output=True,
            text=True,
            timeout=5,
        )
        assert result.returncode == 0


# ---------------------------------------------------------------------------
# Scenario: Fallback Calculation (no used_percentage)
# ---------------------------------------------------------------------------
class TestFallbackCalculation:
    def test_calculates_from_tokens_when_no_native_pct(self):
        """R1: When used_percentage is absent, calculate from tokens."""
        stdin = _make_stdin(
            used_pct=None,  # No native percentage
            ctx_size=200000,
            input_tokens=50000,
            cache_create=30000,
            cache_read=20000,
        )
        out = _strip_ansi(_run_statusline(stdin))
        # (50k+30k+20k)/200k = 50%
        assert "50%" in out
