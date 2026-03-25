"""Tests for BUG-002/BUG-003: Board section placement, auto-move, and status naming."""


BOARD_TEMPLATE = """# Sprint Board

## 📋 Backlog
| ID | Title | Priority | Status |
|----|-------|----------|--------|
|    |       |          |        |

## 🔄 In Progress
| ID | Title | Owner | Notes |
|----|-------|-------|-------|
|    |       |       |       |

## ✅ Done
| ID | Title | Completed |
|----|-------|-----------|
|    |       |           |
"""


def _setup_board(tmp_path, content=None):
    """Create a board file in tmp_path and chdir to it."""
    board_dir = tmp_path / 'docs' / 'product'
    board_dir.mkdir(parents=True, exist_ok=True)
    board_file = board_dir / 'sprint_board.md'
    board_file.write_text(content or BOARD_TEMPLATE, encoding='utf-8')
    return board_file


def _board():
    from pactkit.skills import board
    return board


# ---------------------------------------------------------------------------
# Scenario 1: add_story Inserts Under Backlog
# ---------------------------------------------------------------------------
class TestAddStoryUnderBacklog:
    """S1: Story appears between Backlog header and In Progress header."""

    def test_story_before_in_progress(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _setup_board(tmp_path)
        b = _board()
        b.add_story('STORY-100', 'Test Story', 'Task 1')
        content = (tmp_path / 'docs' / 'product' / 'sprint_board.md').read_text()
        backlog_pos = content.index('## 📋 Backlog')
        in_progress_pos = content.index('## 🔄 In Progress')
        story_pos = content.index('### [STORY-100]')
        assert backlog_pos < story_pos < in_progress_pos

    def test_story_not_at_eof(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _setup_board(tmp_path)
        b = _board()
        b.add_story('STORY-100', 'Test Story', 'Task 1')
        content = (tmp_path / 'docs' / 'product' / 'sprint_board.md').read_text()
        # Story should NOT be after Done section
        done_pos = content.index('## ✅ Done')
        story_pos = content.index('### [STORY-100]')
        assert story_pos < done_pos


# ---------------------------------------------------------------------------
# Scenario 2: Multiple Stories Maintain Order
# ---------------------------------------------------------------------------
class TestMultipleStoriesOrder:
    """S2: Second story appears after first, still before In Progress."""

    def test_two_stories_ordered(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _setup_board(tmp_path)
        b = _board()
        b.add_story('STORY-100', 'First Story', 'Task A')
        b.add_story('STORY-101', 'Second Story', 'Task B')
        content = (tmp_path / 'docs' / 'product' / 'sprint_board.md').read_text()
        s100_pos = content.index('### [STORY-100]')
        s101_pos = content.index('### [STORY-101]')
        in_progress_pos = content.index('## 🔄 In Progress')
        assert s100_pos < s101_pos < in_progress_pos


# ---------------------------------------------------------------------------
# Scenario 3: fix_board Relocates Misplaced Stories
# ---------------------------------------------------------------------------
class TestFixBoard:
    """S3: fix_board moves stories from EOF to correct sections."""

    def test_relocate_todo_to_backlog(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        # Simulate the old bug: story appended after Done
        broken_board = BOARD_TEMPLATE + "\n\n### [STORY-200] Misplaced\n> Spec: docs/specs/STORY-200.md\n\n- [ ] Unchecked task\n"
        _setup_board(tmp_path, broken_board)
        b = _board()
        b.fix_board()
        content = (tmp_path / 'docs' / 'product' / 'sprint_board.md').read_text()
        backlog_pos = content.index('## 📋 Backlog')
        in_progress_pos = content.index('## 🔄 In Progress')
        story_pos = content.index('### [STORY-200]')
        assert backlog_pos < story_pos < in_progress_pos

    def test_relocate_mixed_to_in_progress(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        broken_board = BOARD_TEMPLATE + "\n\n### [STORY-201] Mixed\n> Spec: docs/specs/STORY-201.md\n\n- [x] Done task\n- [ ] Open task\n"
        _setup_board(tmp_path, broken_board)
        b = _board()
        b.fix_board()
        content = (tmp_path / 'docs' / 'product' / 'sprint_board.md').read_text()
        in_progress_pos = content.index('## 🔄 In Progress')
        done_pos = content.index('## ✅ Done')
        story_pos = content.index('### [STORY-201]')
        assert in_progress_pos < story_pos < done_pos

    def test_relocate_complete_to_done(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        broken_board = BOARD_TEMPLATE + "\n\n### [STORY-202] Complete\n> Spec: docs/specs/STORY-202.md\n\n- [x] All done\n"
        _setup_board(tmp_path, broken_board)
        b = _board()
        b.fix_board()
        content = (tmp_path / 'docs' / 'product' / 'sprint_board.md').read_text()
        done_pos = content.index('## ✅ Done')
        story_pos = content.index('### [STORY-202]')
        assert story_pos > done_pos


# ---------------------------------------------------------------------------
# Scenario 4: Existing Functions Still Work
# ---------------------------------------------------------------------------
class TestExistingFunctionsWork:
    """S4: list_stories, update_task, archive_stories work after fix."""

    def test_list_stories_works(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _setup_board(tmp_path)
        b = _board()
        b.add_story('STORY-100', 'Test Story', 'Task 1')
        result = b.list_stories()
        assert 'STORY-100' in result
        assert 'BACKLOG' in result

    def test_update_task_works(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _setup_board(tmp_path)
        b = _board()
        b.add_story('STORY-100', 'Test Story', 'Task 1')
        result = b.update_task('STORY-100', ['Task', '1'])
        assert '✅' in result

    def test_archive_works(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _setup_board(tmp_path)
        (tmp_path / 'docs' / 'product' / 'archive').mkdir(parents=True, exist_ok=True)
        b = _board()
        b.add_story('STORY-100', 'Test Story', 'Task 1')
        b.update_task('STORY-100', ['Task', '1'])
        result = b.archive_stories()
        assert '✅' in result or 'Archived' in result


# ---------------------------------------------------------------------------
# Scenario 5: CLI Subcommand Available
# ---------------------------------------------------------------------------
class TestFixBoardCli:
    """S5: fix_board is callable as a function."""

    def test_fix_board_exists(self):
        b = _board()
        assert hasattr(b, 'fix_board')
        assert callable(b.fix_board)

    def test_fix_board_on_clean_board(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _setup_board(tmp_path)
        b = _board()
        result = b.fix_board()
        assert '✅' in result or 'No misplaced' in result


# ---------------------------------------------------------------------------
# Extra: Section headers preserved after operations
# ---------------------------------------------------------------------------
class TestSectionHeadersPreserved:
    """R3: All three section headers survive add_story and fix_board."""

    def test_headers_after_add(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _setup_board(tmp_path)
        b = _board()
        b.add_story('STORY-100', 'Test', 'Task 1')
        content = (tmp_path / 'docs' / 'product' / 'sprint_board.md').read_text()
        assert '## 📋 Backlog' in content
        assert '## 🔄 In Progress' in content
        assert '## ✅ Done' in content

    def test_headers_after_fix(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        broken = BOARD_TEMPLATE + "\n### [STORY-300] Orphan\n- [ ] task\n"
        _setup_board(tmp_path, broken)
        b = _board()
        b.fix_board()
        content = (tmp_path / 'docs' / 'product' / 'sprint_board.md').read_text()
        assert '## 📋 Backlog' in content
        assert '## 🔄 In Progress' in content
        assert '## ✅ Done' in content


# ---------------------------------------------------------------------------
# BUG-003 Scenario 1: Story Auto-Moves to In Progress
# ---------------------------------------------------------------------------
class TestAutoMoveToInProgress:
    """BUG-003 S1: update_task moves story from Backlog to In Progress."""

    def test_update_task_moves_to_in_progress(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _setup_board(tmp_path)
        b = _board()
        b.add_story('STORY-100', 'Test Story', 'Task A|Task B')
        b.update_task('STORY-100', ['Task', 'A'])
        content = (tmp_path / 'docs' / 'product' / 'sprint_board.md').read_text()
        in_progress_pos = content.index('## 🔄 In Progress')
        done_pos = content.index('## ✅ Done')
        story_pos = content.index('### [STORY-100]')
        assert in_progress_pos < story_pos < done_pos


# ---------------------------------------------------------------------------
# BUG-003 Scenario 2: Story Auto-Moves to Done
# ---------------------------------------------------------------------------
class TestAutoMoveToDone:
    """BUG-003 S2: update_task moves story to Done when all tasks checked."""

    def test_update_last_task_moves_to_done(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _setup_board(tmp_path)
        b = _board()
        b.add_story('STORY-100', 'Test Story', 'Task A|Task B')
        b.update_task('STORY-100', ['Task', 'A'])
        b.update_task('STORY-100', ['Task', 'B'])
        content = (tmp_path / 'docs' / 'product' / 'sprint_board.md').read_text()
        done_pos = content.index('## ✅ Done')
        story_pos = content.index('### [STORY-100]')
        assert story_pos > done_pos


# ---------------------------------------------------------------------------
# BUG-003 Scenario 3: Story Stays in Backlog
# ---------------------------------------------------------------------------
class TestStaysInBacklog:
    """BUG-003 S3: Story with no updates remains in Backlog."""

    def test_no_update_stays_in_backlog(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _setup_board(tmp_path)
        b = _board()
        b.add_story('STORY-100', 'Test Story', 'Task A|Task B')
        content = (tmp_path / 'docs' / 'product' / 'sprint_board.md').read_text()
        backlog_pos = content.index('## 📋 Backlog')
        in_progress_pos = content.index('## 🔄 In Progress')
        story_pos = content.index('### [STORY-100]')
        assert backlog_pos < story_pos < in_progress_pos


# ---------------------------------------------------------------------------
# BUG-003 Scenario 4: list_stories Uses BACKLOG Label
# ---------------------------------------------------------------------------
class TestListStoriesBacklogLabel:
    """BUG-003 S4: list_stories reports BACKLOG instead of TODO."""

    def test_backlog_label(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _setup_board(tmp_path)
        b = _board()
        b.add_story('STORY-100', 'Test Story', 'Task 1')
        result = b.list_stories()
        assert 'BACKLOG' in result
        assert 'TODO' not in result

    def test_in_progress_label(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _setup_board(tmp_path)
        b = _board()
        b.add_story('STORY-100', 'Test Story', 'Task A|Task B')
        b.update_task('STORY-100', ['Task', 'A'])
        result = b.list_stories()
        assert 'IN_PROGRESS' in result

    def test_done_label(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _setup_board(tmp_path)
        b = _board()
        b.add_story('STORY-100', 'Test Story', 'Task 1')
        b.update_task('STORY-100', ['Task', '1'])
        result = b.list_stories()
        assert 'DONE' in result
