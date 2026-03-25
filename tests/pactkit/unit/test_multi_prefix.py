"""STORY-032: Multi-Prefix Work Item Support (STORY/HOTFIX/BUG)."""
import os
import sys
from pathlib import Path
from unittest.mock import patch

project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


def _load_board_ns(board_content, tmp_path):
    """Load board.py functions with a prepared board file."""
    board_dir = tmp_path / 'docs' / 'product'
    board_dir.mkdir(parents=True, exist_ok=True)
    (board_dir / 'sprint_board.md').write_text(board_content, encoding='utf-8')
    src = (project_root / 'src' / 'pactkit' / 'skills' / 'board.py').read_text()
    ns = {}
    exec(compile(src, 'board.py', 'exec'), ns)
    return ns


def _load_scaffold_ns():
    """Load scaffold.py functions."""
    src = (project_root / 'src' / 'pactkit' / 'skills' / 'scaffold.py').read_text()
    ns = {}
    exec(compile(src, 'scaffold.py', 'exec'), ns)
    return ns


MULTI_PREFIX_BOARD = """\
# Sprint Board

## 📋 Backlog
| ID | Title | Priority | Status |
|----|-------|----------|--------|

### [STORY-001] Feature A
> Spec: docs/specs/STORY-001.md

- [ ] Task A

### [HOTFIX-001] Fix typo
> Spec: docs/specs/HOTFIX-001.md

- [x] Fix the typo

### [BUG-001] Login crash
> Spec: docs/specs/BUG-001.md

- [ ] Investigate
- [x] Fix null check
"""


class TestListStoriesMultiPrefix:
    """Scenario 1: list_stories recognizes multi-prefix items."""

    def test_list_stories_finds_all_prefixes(self, tmp_path):
        ns = _load_board_ns(MULTI_PREFIX_BOARD, tmp_path)
        with patch('os.getcwd', return_value=str(tmp_path)):
            os.chdir(tmp_path)
            result = ns['list_stories']()
        assert 'STORY-001' in result
        assert 'HOTFIX-001' in result
        assert 'BUG-001' in result

    def test_list_stories_shows_correct_status(self, tmp_path):
        ns = _load_board_ns(MULTI_PREFIX_BOARD, tmp_path)
        os.chdir(tmp_path)
        result = ns['list_stories']()
        # HOTFIX-001 has all tasks done
        for line in result.splitlines():
            if 'HOTFIX-001' in line:
                assert 'DONE' in line


class TestArchiveMultiPrefix:
    """Scenario 2: archive_stories handles multi-prefix items."""

    def test_archive_hotfix_item(self, tmp_path):
        ns = _load_board_ns(MULTI_PREFIX_BOARD, tmp_path)
        os.chdir(tmp_path)
        result = ns['archive_stories']()
        assert 'Archived' in result
        # HOTFIX-001 (all done) should be archived
        archive_dir = tmp_path / 'docs' / 'product' / 'archive'
        archive_files = list(archive_dir.glob('archive_*.md'))
        assert len(archive_files) == 1
        archive_content = archive_files[0].read_text()
        assert 'HOTFIX-001' in archive_content
        # Board should still have STORY-001 and BUG-001
        board = (tmp_path / 'docs' / 'product' / 'sprint_board.md').read_text()
        assert 'STORY-001' in board
        assert 'BUG-001' in board
        assert 'HOTFIX-001' not in board


class TestGitStartBranchMapping:
    """Scenario 3 & 4: git_start maps prefix to branch type."""

    def _get_branch_from_git_start(self, ns, item_id):
        """Call git_start with mocked subprocess and return the branch name."""
        with patch.dict(ns, {'subprocess': type(sys)('mock_sp')}):
            branches = []
            def fake_run(cmd, **kw):
                branches.append(cmd[-1])
            with patch('subprocess.run', side_effect=fake_run):
                # Re-exec with patched subprocess
                ns_fresh = _load_scaffold_ns()
                with patch('subprocess.run', side_effect=fake_run):
                    ns_fresh['git_start'](item_id)
            return branches[0] if branches else ''

    def test_hotfix_creates_fix_branch(self):
        ns = _load_scaffold_ns()
        branch = self._get_branch_from_git_start(ns, 'HOTFIX-001')
        assert branch.startswith('fix/'), f'Expected fix/ branch, got: {branch}'
        assert 'HOTFIX-001' in branch

    def test_story_creates_feature_branch(self):
        ns = _load_scaffold_ns()
        branch = self._get_branch_from_git_start(ns, 'STORY-033')
        assert branch.startswith('feature/'), f'Expected feature/ branch, got: {branch}'
        assert 'STORY-033' in branch

    def test_bug_creates_fix_branch(self):
        ns = _load_scaffold_ns()
        branch = self._get_branch_from_git_start(ns, 'BUG-001')
        assert branch.startswith('fix/'), f'Expected fix/ branch, got: {branch}'
        assert 'BUG-001' in branch


class TestHotfixPromptTraceability:
    """Scenario 5: Hotfix generates lightweight Spec and Board entry."""

    def test_hotfix_prompt_mentions_spec_creation(self):
        from pactkit.prompts import HOTFIX_PROMPT
        lower = HOTFIX_PROMPT.lower()
        assert 'spec' in lower and 'create' in lower, \
            'HOTFIX_PROMPT must instruct creating a Spec'

    def test_hotfix_prompt_mentions_board_entry(self):
        from pactkit.prompts import HOTFIX_PROMPT
        lower = HOTFIX_PROMPT.lower()
        assert 'board' in lower and 'add' in lower, \
            'HOTFIX_PROMPT must instruct adding a Board entry'

    def test_hotfix_prompt_mentions_hotfix_id(self):
        from pactkit.prompts import HOTFIX_PROMPT
        assert 'HOTFIX-' in HOTFIX_PROMPT, \
            'HOTFIX_PROMPT must reference HOTFIX- prefix'


class TestHierarchyRuleGlob:
    """Scenario 6: Hierarchy rule uses multi-prefix glob."""

    def test_hierarchy_not_limited_to_story_glob(self):
        from pactkit.prompts import RULES_MODULES
        hierarchy = RULES_MODULES['hierarchy']
        # Must NOT contain the old pattern that only matches STORY-*
        assert 'STORY-*.md' not in hierarchy, \
            'Hierarchy rule still hardcodes STORY-*.md glob'
