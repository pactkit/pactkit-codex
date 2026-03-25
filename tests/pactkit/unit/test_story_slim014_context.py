"""Tests for pactkit context (STORY-slim-014 R1).

Scenario: pactkit context generates docs/product/context.md from board + git + lessons.
"""
from pathlib import Path
from unittest.mock import patch

from pactkit.context_gen import generate_context
from pactkit.schemas import (
    BOARD_SECTION_BACKLOG,
    BOARD_SECTION_DONE,
    BOARD_SECTION_IN_PROGRESS,
    CONTEXT_SECTIONS,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_board(tmp_path: Path, *, backlog: int = 0, in_progress: int = 0, done: int = 0) -> None:
    """Write a minimal sprint_board.md to tmp_path using canonical section headers."""
    lines = [BOARD_SECTION_BACKLOG]
    for i in range(backlog):
        lines += [
            "",
            f"### [STORY-slim-{900 + i:03d}] Backlog story {i}",
            "- [ ] task one",
        ]
    lines += ["", BOARD_SECTION_IN_PROGRESS]
    for i in range(in_progress):
        lines += [
            "",
            f"### [STORY-slim-{800 + i:03d}] In-progress story {i}",
            "- [x] done task",
            "- [ ] todo task",
        ]
    lines += ["", BOARD_SECTION_DONE]
    for i in range(done):
        lines += [
            "",
            f"### [STORY-slim-{700 + i:03d}] Done story {i}",
            "- [x] all done",
        ]

    board_path = tmp_path / "docs" / "product"
    board_path.mkdir(parents=True, exist_ok=True)
    (board_path / "sprint_board.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _mock_git_branch():
    """Patch subprocess.run to return a canned git branch output."""
    return patch(
        "pactkit.context_gen.subprocess.run",
        return_value=type("R", (), {"stdout": "* main\n  feature/STORY-slim-014\n", "returncode": 0})(),
    )


# ---------------------------------------------------------------------------
# Tests: Sprint Status section
# ---------------------------------------------------------------------------

class TestSprintStatusSection:
    """The generated context must report Backlog / In Progress / Done counts."""

    def test_backlog_count_in_status(self, tmp_path):
        """Given 1 backlog story → output contains 'Backlog: 1'."""
        _make_board(tmp_path, backlog=1)
        with _mock_git_branch():
            result = generate_context(tmp_path)
        assert "Backlog: 1" in result

    def test_in_progress_count(self, tmp_path):
        """Given 1 in-progress story → output contains 'In Progress: 1'."""
        _make_board(tmp_path, in_progress=1)
        with _mock_git_branch():
            result = generate_context(tmp_path)
        assert "In Progress: 1" in result

    def test_done_count(self, tmp_path):
        """Given 2 done stories → output contains 'Done: 2'."""
        _make_board(tmp_path, done=2)
        with _mock_git_branch():
            result = generate_context(tmp_path)
        assert "Done: 2" in result

    def test_sprint_status_header_present(self, tmp_path):
        """## Sprint Status section is always present."""
        _make_board(tmp_path)
        with _mock_git_branch():
            result = generate_context(tmp_path)
        assert "## Sprint Status" in result


# ---------------------------------------------------------------------------
# Tests: Board missing fallback
# ---------------------------------------------------------------------------

class TestBoardMissingFallback:
    """When sprint_board.md doesn't exist, output graceful fallback."""

    def test_no_board_fallback(self, tmp_path):
        """Given no board → output contains 'No board found' (case-insensitive)."""
        with _mock_git_branch():
            result = generate_context(tmp_path)
        assert "no board" in result.lower() or "sprint status" in result.lower()

    def test_no_board_still_has_all_sections(self, tmp_path):
        """Even with missing board, all CONTEXT_SECTIONS headers are present."""
        with _mock_git_branch():
            result = generate_context(tmp_path)
        for section in CONTEXT_SECTIONS:
            assert section in result, f"Missing section: {section!r}"


# ---------------------------------------------------------------------------
# Tests: All canonical sections present
# ---------------------------------------------------------------------------

class TestAllSectionsPresent:
    """The generated context MUST contain every CONTEXT_SECTIONS header."""

    def test_all_context_sections(self, tmp_path):
        """Output includes every header from CONTEXT_SECTIONS."""
        _make_board(tmp_path, backlog=1)
        with _mock_git_branch():
            result = generate_context(tmp_path)
        for section in CONTEXT_SECTIONS:
            assert section in result, f"Missing section: {section!r}"


# ---------------------------------------------------------------------------
# Tests: Timestamp and command name
# ---------------------------------------------------------------------------

class TestTimestampAndCommand:
    """The 'Last updated' header must include ISO timestamp and command name."""

    def test_timestamp_iso_format(self, tmp_path):
        """The output contains a timestamp in ISO-like format (YYYY-MM-DD)."""
        _make_board(tmp_path)
        with _mock_git_branch():
            result = generate_context(tmp_path)
        # ISO date portion: YYYY-MM-DD
        import re
        assert re.search(r"\d{4}-\d{2}-\d{2}", result), "No ISO date found in output"

    def test_last_updated_line(self, tmp_path):
        """The output contains a 'Last updated' line."""
        _make_board(tmp_path)
        with _mock_git_branch():
            result = generate_context(tmp_path)
        assert "Last updated" in result

    def test_command_name_appears(self, tmp_path):
        """The command name passed to generate_context() appears in the output."""
        _make_board(tmp_path)
        with _mock_git_branch():
            result = generate_context(tmp_path, command="pactkit context")
        assert "pactkit context" in result

    def test_custom_command_name(self, tmp_path):
        """A custom command string is reflected in the header."""
        _make_board(tmp_path)
        with _mock_git_branch():
            result = generate_context(tmp_path, command="/project-done")
        assert "/project-done" in result


# ---------------------------------------------------------------------------
# Tests: Active Branches section
# ---------------------------------------------------------------------------

class TestActiveBranchesSection:
    """Active Branches section is populated from git output."""

    def test_active_branches_section_present(self, tmp_path):
        """## Active Branches section is in the output."""
        _make_board(tmp_path)
        with _mock_git_branch():
            result = generate_context(tmp_path)
        assert "## Active Branches" in result

    def test_git_branch_output_included(self, tmp_path):
        """Branch names from mocked git appear in output."""
        _make_board(tmp_path)
        with _mock_git_branch():
            result = generate_context(tmp_path)
        assert "main" in result


# ---------------------------------------------------------------------------
# Tests: Context header
# ---------------------------------------------------------------------------

class TestContextHeader:
    """The generated content starts with the canonical header."""

    def test_starts_with_canonical_header(self, tmp_path):
        """Output starts with '# Project Context (Auto-generated)'."""
        from pactkit.schemas import CONTEXT_HEADER
        _make_board(tmp_path)
        with _mock_git_branch():
            result = generate_context(tmp_path)
        assert result.startswith(CONTEXT_HEADER)


# ---------------------------------------------------------------------------
# Tests: Return type
# ---------------------------------------------------------------------------

class TestReturnType:
    """generate_context() returns a str and does NOT write files."""

    def test_returns_string(self, tmp_path):
        """Return type is str."""
        _make_board(tmp_path)
        with _mock_git_branch():
            result = generate_context(tmp_path)
        assert isinstance(result, str)

    def test_does_not_write_context_file(self, tmp_path):
        """generate_context() must NOT write docs/product/context.md."""
        _make_board(tmp_path)
        context_file = tmp_path / "docs" / "product" / "context.md"
        with _mock_git_branch():
            generate_context(tmp_path)
        assert not context_file.exists(), "generate_context() must not write the file"
