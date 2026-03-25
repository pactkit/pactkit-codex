"""Tests for P1: update_task must actually modify sprint_board.md."""
import textwrap

import pytest

BOARD_TEMPLATE = textwrap.dedent("""\
# Sprint Board

## Backlog
| ID | Title | Priority | Status |
|----|-------|----------|--------|
|    |       |          |        |


### [STORY-001] User Login
> Spec: docs/specs/STORY-001.md

- [ ] T1:Design API
- [ ] T2:Write tests
- [x] T3:Setup DB

### [STORY-002] User Signup
> Spec: docs/specs/STORY-002.md

- [ ] T1:Create form
- [ ] T2:Validate input
""")


@pytest.fixture
def board_dir(tmp_path):
    """Create a temporary board file and chdir to its parent."""
    docs = tmp_path / 'docs' / 'product'
    docs.mkdir(parents=True)
    board = docs / 'sprint_board.md'
    board.write_text(BOARD_TEMPLATE, encoding='utf-8')
    import os
    original = os.getcwd()
    os.chdir(tmp_path)
    yield tmp_path
    os.chdir(original)


def _import_update_task():
    """Import update_task from board.py resource script."""
    import importlib

    import pactkit.skills.board as board_mod
    importlib.reload(board_mod)
    return board_mod.update_task


class TestUpdateTaskModifiesFile:
    """P1: update_task MUST modify sprint_board.md, not just return a string."""

    def test_marks_task_done(self, board_dir):
        update_task = _import_update_task()
        result = update_task('STORY-001', ['T1:Design API'])
        board = (board_dir / 'docs/product/sprint_board.md').read_text()
        assert '- [x] T1:Design API' in board

    def test_returns_success_message(self, board_dir):
        update_task = _import_update_task()
        result = update_task('STORY-001', ['T1:Design API'])
        assert 'T1:Design API' in result
        assert '✅' in result

    def test_does_not_touch_other_stories(self, board_dir):
        update_task = _import_update_task()
        update_task('STORY-001', ['T1:Design API'])
        board = (board_dir / 'docs/product/sprint_board.md').read_text()
        # STORY-002 tasks should remain unchecked
        assert '- [ ] T1:Create form' in board
        assert '- [ ] T2:Validate input' in board

    def test_does_not_touch_other_tasks_same_story(self, board_dir):
        update_task = _import_update_task()
        update_task('STORY-001', ['T1:Design API'])
        board = (board_dir / 'docs/product/sprint_board.md').read_text()
        assert '- [ ] T2:Write tests' in board

    def test_already_done_task(self, board_dir):
        update_task = _import_update_task()
        # T3 is already [x] in the template
        result = update_task('STORY-001', ['T3:Setup DB'])
        assert 'already' in result.lower() or '✅' in result

    def test_story_not_found(self, board_dir):
        update_task = _import_update_task()
        result = update_task('STORY-999', ['T1:Foo'])
        assert '❌' in result or 'not found' in result.lower()

    def test_task_not_found_in_story(self, board_dir):
        update_task = _import_update_task()
        result = update_task('STORY-001', ['T9:Nonexistent'])
        assert '❌' in result or 'not found' in result.lower()

    def test_no_board_file(self, tmp_path):
        import os
        original = os.getcwd()
        os.chdir(tmp_path)
        try:
            update_task = _import_update_task()
            result = update_task('STORY-001', ['T1:Foo'])
            assert 'No Board' in result
        finally:
            os.chdir(original)

    def test_multiple_tasks_in_args(self, board_dir):
        """update_task receives nargs='+', joining space-separated args."""
        update_task = _import_update_task()
        result = update_task('STORY-001', ['T2:Write', 'tests'])
        board = (board_dir / 'docs/product/sprint_board.md').read_text()
        assert '- [x] T2:Write tests' in board

    def test_preserves_board_structure(self, board_dir):
        update_task = _import_update_task()
        update_task('STORY-001', ['T1:Design API'])
        board = (board_dir / 'docs/product/sprint_board.md').read_text()
        assert '# Sprint Board' in board
        assert '### [STORY-001]' in board
        assert '### [STORY-002]' in board
