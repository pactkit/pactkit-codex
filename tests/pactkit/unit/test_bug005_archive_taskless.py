"""BUG-005: board.py archive vs classify inconsistent for taskless stories.

archive_stories() must NOT archive stories that have zero tasks.
Only stories with all tasks checked `[x]` should be archived.
"""
from pactkit.skills.board import archive_stories


def _make_board(tmp_path, stories_md):
    """Write a sprint board with the given stories section and return the board path."""
    board = tmp_path / "docs" / "product" / "sprint_board.md"
    board.parent.mkdir(parents=True, exist_ok=True)
    content = f"# Sprint Board\n\n## 📋 Backlog\n{stories_md}\n## 🔄 In Progress\n\n## ✅ Done\n\n"
    board.write_text(content, encoding="utf-8")
    return board


class TestTasklessStoryNotArchived:
    """A story with no task checkboxes must NOT be archived."""

    def test_taskless_story_stays_on_board(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _make_board(tmp_path, "\n### [STORY-099] Taskless Story\n> Spec: docs/specs/STORY-099.md\n")

        result = archive_stories()

        assert "No completed stories" in result
        board = (tmp_path / "docs" / "product" / "sprint_board.md").read_text()
        assert "STORY-099" in board, "Taskless story should remain on board"

    def test_taskless_story_not_in_archive(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _make_board(tmp_path, "\n### [STORY-099] Taskless Story\n> Spec: docs/specs/STORY-099.md\n")

        archive_stories()

        archive_dir = tmp_path / "docs" / "product" / "archive"
        if archive_dir.exists():
            for f in archive_dir.glob("*.md"):
                content = f.read_text()
                assert "STORY-099" not in content, "Taskless story was incorrectly archived"


class TestAllDoneStoryStillArchived:
    """A story with all tasks [x] must still be archived (existing behavior)."""

    def test_completed_story_archived(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        stories = "\n### [STORY-100] Completed Story\n> Spec: docs/specs/STORY-100.md\n\n- [x] Task A\n- [x] Task B\n"
        _make_board(tmp_path, stories)

        result = archive_stories()

        assert "Archived 1" in result
        board = (tmp_path / "docs" / "product" / "sprint_board.md").read_text()
        assert "STORY-100" not in board


class TestUncheckedStoryNotArchived:
    """A story with unchecked tasks must NOT be archived (existing behavior)."""

    def test_incomplete_story_stays(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        stories = "\n### [STORY-101] WIP Story\n> Spec: docs/specs/STORY-101.md\n\n- [x] Task A\n- [ ] Task B\n"
        _make_board(tmp_path, stories)

        result = archive_stories()

        assert "No completed stories" in result
        board = (tmp_path / "docs" / "product" / "sprint_board.md").read_text()
        assert "STORY-101" in board
