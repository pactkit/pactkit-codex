"""STORY-015: list_stories() unit tests — strict TDD."""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


def _load_board_funcs():
    """Load board functions via exec(TOOLS_SOURCE) — same pattern as test_tools.py."""
    import pactkit.prompts as p

    ns = {}
    exec(p.TOOLS_SOURCE, ns)
    return ns


def _setup_board(tmp_path, content):
    board_dir = tmp_path / "docs" / "product"
    board_dir.mkdir(parents=True)
    board_path = board_dir / "sprint_board.md"
    board_path.write_text(content, encoding="utf-8")
    return board_path


class TestListStoriesMultiple:
    """Scenario 1: Board with multiple stories — correct output with counts and status."""

    def test_multi_story_output(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        board_md = """\
# Sprint Board

### [STORY-014] Implement Sprint orchestration
> Spec: docs/specs/STORY-014.md

- [x] T1:Design subagent prompt
- [x] T2:Create sprint command
- [x] T3:Add parallel check
- [x] T4:Write unit tests
- [x] T5:Update prompts.py
- [ ] T6:E2E validation

### [STORY-015] Add list_stories subcommand
> Spec: docs/specs/STORY-015.md

- [ ] T1:Write unit tests
- [ ] T2:Implement list_stories
- [ ] T3:Register CLI
- [ ] T4:Update prompts.py
"""
        _setup_board(tmp_path, board_md)
        ns = _load_board_funcs()

        result = ns["list_stories"]()

        # STORY-014: 5/6 IN_PROGRESS
        assert "STORY-014" in result
        assert "5/6" in result
        assert "IN_PROGRESS" in result

        # STORY-015: 0/4 BACKLOG
        assert "STORY-015" in result
        assert "0/4" in result
        assert "BACKLOG" in result

    def test_stories_appear_in_id_order(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        # Intentionally put 015 before 014 in file to test sorting
        board_md = """\
# Sprint Board

### [STORY-015] Second story
> Spec: docs/specs/STORY-015.md

- [ ] T1:Task

### [STORY-014] First story
> Spec: docs/specs/STORY-014.md

- [x] T1:Task
"""
        _setup_board(tmp_path, board_md)
        ns = _load_board_funcs()

        result = ns["list_stories"]()
        idx_014 = result.index("STORY-014")
        idx_015 = result.index("STORY-015")
        assert idx_014 < idx_015, "Stories should be sorted by ID"


class TestListStoriesEmpty:
    """Scenario 2: Board exists but has no stories."""

    def test_no_stories_message(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        board_md = """\
# Sprint Board

Sprint 20.0 — PactKit Core
"""
        _setup_board(tmp_path, board_md)
        ns = _load_board_funcs()

        result = ns["list_stories"]()
        assert result == "No stories on board."


class TestListStoriesMissingBoard:
    """Scenario 3: Board file does not exist."""

    def test_no_board_returns_error(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        ns = _load_board_funcs()

        result = ns["list_stories"]()
        assert "No Board" in result


class TestListStoriesAllDone:
    """Scenario 4: All tasks in a story are complete -> DONE."""

    def test_all_tasks_done_status(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        board_md = """\
# Sprint Board

### [STORY-010] Fully completed story
> Spec: docs/specs/STORY-010.md

- [x] T1:First task
- [x] T2:Second task
- [x] T3:Third task
"""
        _setup_board(tmp_path, board_md)
        ns = _load_board_funcs()

        result = ns["list_stories"]()
        assert "STORY-010" in result
        assert "3/3" in result
        assert "DONE" in result
        # Must NOT say IN_PROGRESS for this story
        lines = result.strip().splitlines()
        for line in lines:
            if "STORY-010" in line:
                assert "IN_PROGRESS" not in line


class TestListStoriesBackwardCompat:
    """Scenario 5: Existing subcommands still work after adding list_stories."""

    def test_add_story_still_works(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        board_dir = tmp_path / "docs" / "product"
        board_dir.mkdir(parents=True)
        (board_dir / "sprint_board.md").write_text("# Sprint Board\n", encoding="utf-8")

        ns = _load_board_funcs()
        result = ns["add_story"]("STORY-TEST", "Test Story", "T1:foo|T2:bar")
        assert "STORY-TEST" in result
        board = (board_dir / "sprint_board.md").read_text()
        assert "STORY-TEST" in board

    def test_archive_still_works(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        board_md = """\
# Sprint Board

### [STORY-001] Done
> Spec: docs/specs/STORY-001.md

- [x] T1:Done
"""
        _setup_board(tmp_path, board_md)
        ns = _load_board_funcs()
        result = ns["archive_stories"]()
        assert "Archived" in result or "archive" in result.lower()

    def test_list_stories_registered_in_cli(self):
        """Verify list_stories appears in the CLI block of TOOLS_SOURCE."""
        import pactkit.prompts as p

        assert "list_stories" in p.BOARD_SOURCE
        assert 'a.cmd == "list_stories"' in p.BOARD_SOURCE or "a.cmd == 'list_stories'" in p.BOARD_SOURCE

    def test_skill_board_md_documents_list_stories(self):
        """R4: SKILL_BOARD_MD must mention list_stories."""
        import pactkit.prompts as p

        assert "list_stories" in p.SKILL_BOARD_MD
