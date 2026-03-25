"""Tests for BUG-006: visualize _scan_files exclude list for marketplace deployment.

AC1: Marketplace-deployed dirs (skills, commands, rules, agents) excluded from scan
AC2: Classic deployment unaffected (PactKit files outside project root)
AC3: Project source files still scanned normally
"""
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from pactkit.skills.visualize import _scan_files  # noqa: E402

# ===========================================================================
# AC1: Marketplace-deployed dirs excluded
# ===========================================================================

class TestAC1MarketplaceExcludes:

    def test_skills_dir_excluded(self, tmp_path):
        """Files under skills/ are excluded from scan."""
        (tmp_path / 'skills').mkdir()
        (tmp_path / 'skills' / 'visualize.py').write_text('x = 1')
        (tmp_path / 'app.py').write_text('y = 2')
        all_files, _, _ = _scan_files(tmp_path)
        names = [f.name for f in all_files]
        assert 'app.py' in names
        assert 'visualize.py' not in names

    def test_commands_dir_excluded(self, tmp_path):
        """Files under commands/ are excluded from scan."""
        (tmp_path / 'commands').mkdir()
        (tmp_path / 'commands' / 'plan.py').write_text('x = 1')
        (tmp_path / 'app.py').write_text('y = 2')
        all_files, _, _ = _scan_files(tmp_path)
        names = [f.name for f in all_files]
        assert 'app.py' in names
        assert 'plan.py' not in names

    def test_rules_dir_excluded(self, tmp_path):
        """Files under rules/ are excluded from scan."""
        (tmp_path / 'rules').mkdir()
        (tmp_path / 'rules' / 'core.py').write_text('x = 1')
        (tmp_path / 'app.py').write_text('y = 2')
        all_files, _, _ = _scan_files(tmp_path)
        names = [f.name for f in all_files]
        assert 'app.py' in names
        assert 'core.py' not in names

    def test_agents_dir_excluded(self, tmp_path):
        """Files under agents/ are excluded from scan."""
        (tmp_path / 'agents').mkdir()
        (tmp_path / 'agents' / 'architect.py').write_text('x = 1')
        (tmp_path / 'app.py').write_text('y = 2')
        all_files, _, _ = _scan_files(tmp_path)
        names = [f.name for f in all_files]
        assert 'app.py' in names
        assert 'architect.py' not in names


# ===========================================================================
# AC2: Existing excludes still work
# ===========================================================================

class TestAC2ExistingExcludes:

    def test_venv_still_excluded(self, tmp_path):
        """Pre-existing venv exclude still works."""
        (tmp_path / 'venv').mkdir()
        (tmp_path / 'venv' / 'lib.py').write_text('x = 1')
        all_files, _, _ = _scan_files(tmp_path)
        names = [f.name for f in all_files]
        assert 'lib.py' not in names

    def test_tests_still_excluded(self, tmp_path):
        """Pre-existing tests exclude still works."""
        (tmp_path / 'tests').mkdir()
        (tmp_path / 'tests' / 'test_foo.py').write_text('x = 1')
        all_files, _, _ = _scan_files(tmp_path)
        names = [f.name for f in all_files]
        assert 'test_foo.py' not in names

    def test_git_still_excluded(self, tmp_path):
        """Pre-existing .git exclude still works."""
        (tmp_path / '.git').mkdir()
        (tmp_path / '.git' / 'hook.py').write_text('x = 1')
        all_files, _, _ = _scan_files(tmp_path)
        names = [f.name for f in all_files]
        assert 'hook.py' not in names


# ===========================================================================
# AC3: Project source files still scanned
# ===========================================================================

class TestAC3ProjectFilesScanned:

    def test_src_dir_scanned(self, tmp_path):
        """Files under src/ are still scanned."""
        (tmp_path / 'src').mkdir()
        (tmp_path / 'src' / 'main.py').write_text('x = 1')
        all_files, _, _ = _scan_files(tmp_path)
        names = [f.name for f in all_files]
        assert 'main.py' in names

    def test_root_py_files_scanned(self, tmp_path):
        """Python files at project root are still scanned."""
        (tmp_path / 'app.py').write_text('x = 1')
        all_files, _, _ = _scan_files(tmp_path)
        names = [f.name for f in all_files]
        assert 'app.py' in names

    def test_nested_src_scanned(self, tmp_path):
        """Nested project source files scanned."""
        (tmp_path / 'src' / 'myapp').mkdir(parents=True)
        (tmp_path / 'src' / 'myapp' / 'models.py').write_text('x = 1')
        all_files, _, _ = _scan_files(tmp_path)
        names = [f.name for f in all_files]
        assert 'models.py' in names


# ===========================================================================
# SCAN_EXCLUDES constant exists
# ===========================================================================

class TestScanExcludesConstant:

    def test_constant_exists(self):
        """SCAN_EXCLUDES constant is defined at module level."""
        from pactkit.skills import visualize
        assert hasattr(visualize, 'SCAN_EXCLUDES')
        assert isinstance(visualize.SCAN_EXCLUDES, (set, frozenset))

    def test_constant_contains_new_excludes(self):
        """SCAN_EXCLUDES includes the 4 new marketplace directories."""
        from pactkit.skills import visualize
        for name in ('skills', 'commands', 'rules', 'agents'):
            assert name in visualize.SCAN_EXCLUDES, f'{name} missing from SCAN_EXCLUDES'

    def test_constant_contains_old_excludes(self):
        """SCAN_EXCLUDES preserves all original excludes."""
        from pactkit.skills import visualize
        original = {'venv', '_venv', '.venv', '.env', 'env', '__pycache__',
                     '.git', '.claude', 'tests', 'docs', 'node_modules',
                     'site-packages', 'dist', 'build'}
        for name in original:
            assert name in visualize.SCAN_EXCLUDES, f'{name} missing from SCAN_EXCLUDES'
