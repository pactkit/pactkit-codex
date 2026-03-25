"""Tests for BUG-024: board.py flexible title regex — bare STORY-xxx: format."""

BOARD_TEMPLATE = """# Sprint Board

## 📋 Backlog

## 🔄 In Progress

## ✅ Done

"""


def _setup_board(tmp_path, content):
    board_dir = tmp_path / 'docs' / 'product'
    board_dir.mkdir(parents=True, exist_ok=True)
    (board_dir / 'sprint_board.md').write_text(content, encoding='utf-8')


def _board():
    from pactkit.skills import board
    return board


# ---------------------------------------------------------------------------
# AC1: Bare title archiving
# ---------------------------------------------------------------------------
class TestAC1BareArchiving:
    """archive_stories() must archive stories with bare STORY-xxx: title."""

    def test_bare_colon_format_archived(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        content = BOARD_TEMPLATE + "### STORY-099: Completed Feature\n\n- [x] Task A\n- [x] Task B\n"
        _setup_board(tmp_path, content)
        (tmp_path / 'docs' / 'product' / 'archive').mkdir(parents=True, exist_ok=True)
        b = _board()
        result = b.archive_stories()
        assert 'Archived' in result, f"Expected archive confirmation, got: {result}"
        board_content = (tmp_path / 'docs' / 'product' / 'sprint_board.md').read_text()
        assert 'STORY-099' not in board_content

    def test_bare_no_colon_format_archived(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        content = BOARD_TEMPLATE + "### STORY-099 Completed Feature\n\n- [x] Task A\n"
        _setup_board(tmp_path, content)
        (tmp_path / 'docs' / 'product' / 'archive').mkdir(parents=True, exist_ok=True)
        b = _board()
        result = b.archive_stories()
        assert 'Archived' in result, f"Expected archive confirmation, got: {result}"
        board_content = (tmp_path / 'docs' / 'product' / 'sprint_board.md').read_text()
        assert 'STORY-099' not in board_content


# ---------------------------------------------------------------------------
# AC2: Bare title listing
# ---------------------------------------------------------------------------
class TestAC2BareListing:
    """list_stories() must return stories with bare BUG-xxx: title."""

    def test_bare_colon_bug_listed(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        content = BOARD_TEMPLATE + "### BUG-050: Fix something\n\n- [ ] Patch it\n"
        _setup_board(tmp_path, content)
        b = _board()
        result = b.list_stories()
        assert 'BUG-050' in result
        assert 'Fix something' in result

    def test_bare_story_listed_with_counts(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        content = BOARD_TEMPLATE + "### STORY-042: Some Title\n\n- [ ] Task 1\n- [ ] Task 2\n"
        _setup_board(tmp_path, content)
        b = _board()
        result = b.list_stories()
        assert 'STORY-042' in result
        assert '0/2' in result
        assert 'BACKLOG' in result


# ---------------------------------------------------------------------------
# AC3: Bare title task update
# ---------------------------------------------------------------------------
class TestAC3BareTaskUpdate:
    """update_task() must toggle tasks in bare HOTFIX-xxx: story."""

    def test_bare_hotfix_task_toggled(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        content = BOARD_TEMPLATE + "### HOTFIX-010: Urgent fix\n\n- [ ] Patch it\n"
        _setup_board(tmp_path, content)
        b = _board()
        result = b.update_task('HOTFIX-010', ['Patch', 'it'])
        assert '✅' in result, f"Expected success, got: {result}"
        board_content = (tmp_path / 'docs' / 'product' / 'sprint_board.md').read_text()
        assert '- [x] Patch it' in board_content

    def test_bare_story_task_toggled(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        content = BOARD_TEMPLATE + "### STORY-050: Some story\n\n- [ ] Do the thing\n"
        _setup_board(tmp_path, content)
        b = _board()
        result = b.update_task('STORY-050', ['Do', 'the', 'thing'])
        assert '✅' in result, f"Expected success, got: {result}"


# ---------------------------------------------------------------------------
# AC4: Bare title fix_board
# ---------------------------------------------------------------------------
class TestAC4BareFixBoard:
    """fix_board() must relocate bare STORY-xxx: entries."""

    def test_bare_all_done_moves_to_done(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        content = BOARD_TEMPLATE + "### STORY-099: Title\n\n- [x] Task 1\n"
        _setup_board(tmp_path, content)
        b = _board()
        result = b.fix_board()
        assert '✅' in result
        board_content = (tmp_path / 'docs' / 'product' / 'sprint_board.md').read_text()
        done_pos = board_content.index('## ✅ Done')
        story_pos = board_content.index('STORY-099')
        assert story_pos > done_pos, "Bare story with all tasks done must appear after Done section"


# ---------------------------------------------------------------------------
# AC5: Bracketed format still works (regression)
# ---------------------------------------------------------------------------
class TestAC5BracketedRegression:
    """### [STORY-100] format must continue to work unchanged."""

    def test_bracketed_archive_unaffected(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        content = BOARD_TEMPLATE + "### [STORY-100] Normal title\n\n- [x] All done\n"
        _setup_board(tmp_path, content)
        (tmp_path / 'docs' / 'product' / 'archive').mkdir(parents=True, exist_ok=True)
        b = _board()
        result = b.archive_stories()
        assert 'Archived' in result
        board_content = (tmp_path / 'docs' / 'product' / 'sprint_board.md').read_text()
        assert 'STORY-100' not in board_content

    def test_bracketed_list_stories_unaffected(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        content = BOARD_TEMPLATE + "### [STORY-100] Normal title\n\n- [ ] Task 1\n"
        _setup_board(tmp_path, content)
        b = _board()
        result = b.list_stories()
        assert 'STORY-100' in result
        assert 'Normal title' in result

    def test_bracketed_update_task_unaffected(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        content = BOARD_TEMPLATE + "### [STORY-100] Normal title\n\n- [ ] Task A\n"
        _setup_board(tmp_path, content)
        b = _board()
        result = b.update_task('STORY-100', ['Task', 'A'])
        assert '✅' in result

    def test_bracketed_fix_board_unaffected(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        content = BOARD_TEMPLATE + "### [STORY-100] Normal title\n\n- [x] All done\n"
        _setup_board(tmp_path, content)
        b = _board()
        result = b.fix_board()
        assert '✅' in result
        board_content = (tmp_path / 'docs' / 'product' / 'sprint_board.md').read_text()
        done_pos = board_content.index('## ✅ Done')
        story_pos = board_content.index('STORY-100')
        assert story_pos > done_pos


# ---------------------------------------------------------------------------
# AC6: add_story canonical format preserved
# ---------------------------------------------------------------------------
class TestAC6AddStoryCanonical:
    """add_story() must still write ### [ID] Title format."""

    def test_add_story_writes_brackets(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        content = "# Sprint Board\n\n## 📋 Backlog\n\n## 🔄 In Progress\n\n## ✅ Done\n"
        _setup_board(tmp_path, content)
        b = _board()
        b.add_story('STORY-101', 'New feature', 'Task A|Task B')
        board_content = (tmp_path / 'docs' / 'product' / 'sprint_board.md').read_text()
        assert '### [STORY-101] New feature' in board_content


# ---------------------------------------------------------------------------
# R2: Normalized ID extraction — both formats yield same ID string
# ---------------------------------------------------------------------------
class TestR2NormalizedExtraction:
    """Both bracketed and bare formats must extract the same ID via list_stories."""

    def test_both_formats_appear_in_listing(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        content = (
            BOARD_TEMPLATE
            + "### [STORY-001] Bracketed\n\n- [ ] Task 1\n\n"
            + "### STORY-002: Bare colon\n\n- [ ] Task 2\n"
        )
        _setup_board(tmp_path, content)
        b = _board()
        result = b.list_stories()
        assert 'STORY-001' in result
        assert 'STORY-002' in result
