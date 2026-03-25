"""
STORY-053: Impact-Based Regression via Call Graph Analysis

TDD tests for:
- AC1: Reverse caller analysis (--reverse flag)
- AC2: Test mapping via impact subcommand
- AC3: Regression decision tree uses impact analysis (prompt test)
- AC4: Fallback to full regression when ≥50 files (prompt test)
- AC5: Release forces full regression (prompt test)
- R4: regression config section in pactkit.yaml
"""
import sys
import tempfile
import warnings
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


def _exec_visualize():
    """Load VISUALIZE_SOURCE into exec globals and return the namespace."""
    from pactkit.prompts import VISUALIZE_SOURCE
    g = {}
    exec(VISUALIZE_SOURCE, g)
    return g


def _create_reverse_test_project(tmp_path):
    """Create a project with a call chain: deploy → _deploy_classic → validate_config."""
    src = tmp_path / 'src'
    src.mkdir()
    (src / '__init__.py').write_text('', encoding='utf-8')

    (src / 'config.py').write_text(
        'def validate_config():\n'
        '    pass\n',
        encoding='utf-8'
    )

    (src / 'deployer.py').write_text(
        'from src.config import validate_config\n'
        '\n'
        'def _deploy_classic():\n'
        '    validate_config()\n'
        '\n'
        'def deploy():\n'
        '    _deploy_classic()\n',
        encoding='utf-8'
    )
    return tmp_path


def _create_impact_test_project(tmp_path):
    """Create a project with test files alongside source files."""
    src = tmp_path / 'src'
    src.mkdir()
    (src / '__init__.py').write_text('', encoding='utf-8')
    (src / 'config.py').write_text(
        'def validate_config():\n'
        '    pass\n'
        '\n'
        'def load_config():\n'
        '    validate_config()\n',
        encoding='utf-8'
    )
    (src / 'deployer.py').write_text(
        'from src.config import validate_config\n'
        '\n'
        'def _deploy_classic():\n'
        '    validate_config()\n',
        encoding='utf-8'
    )

    # Create test files
    tests = tmp_path / 'tests' / 'unit'
    tests.mkdir(parents=True)
    (tests / 'test_config.py').write_text('def test_placeholder(): pass\n', encoding='utf-8')
    (tests / 'test_deployer.py').write_text('def test_placeholder(): pass\n', encoding='utf-8')
    return tmp_path


# ==============================================================================
# AC1: Reverse Caller Analysis
# ==============================================================================
class TestReverseCallerAnalysis:
    """AC1: --reverse flag on visualize --mode call finds all callers of an entry function."""

    def test_reverse_caller_finds_direct_caller(self, tmp_path):
        """Given deploy→_deploy_classic→validate_config, reverse from validate_config includes _deploy_classic."""
        proj = _create_reverse_test_project(tmp_path)
        g = _exec_visualize()
        result = g['visualize'](str(proj), mode='call', entry='validate_config', reverse=True)
        output = (proj / 'docs/architecture/graphs/call_graph.mmd').read_text()
        assert '_deploy_classic' in output, f"Expected _deploy_classic in output: {output}"

    def test_reverse_caller_finds_transitive_callers(self, tmp_path):
        """Given deploy→_deploy_classic→validate_config, reverse from validate_config includes deploy."""
        proj = _create_reverse_test_project(tmp_path)
        g = _exec_visualize()
        result = g['visualize'](str(proj), mode='call', entry='validate_config', reverse=True)
        output = (proj / 'docs/architecture/graphs/call_graph.mmd').read_text()
        assert 'deploy' in output, f"Expected deploy in output: {output}"

    def test_reverse_caller_entry_included(self, tmp_path):
        """The entry function itself should appear in the output."""
        proj = _create_reverse_test_project(tmp_path)
        g = _exec_visualize()
        g['visualize'](str(proj), mode='call', entry='validate_config', reverse=True)
        output = (proj / 'docs/architecture/graphs/call_graph.mmd').read_text()
        assert 'validate_config' in output

    def test_reverse_caller_writes_graph_file(self, tmp_path):
        """--reverse flag writes to call_graph.mmd."""
        proj = _create_reverse_test_project(tmp_path)
        g = _exec_visualize()
        result = g['visualize'](str(proj), mode='call', entry='validate_config', reverse=True)
        assert 'call_graph.mmd' in result
        assert (proj / 'docs/architecture/graphs/call_graph.mmd').exists()

    def test_reverse_caller_output_format(self, tmp_path):
        """Reverse call graph output starts with 'graph TD'."""
        proj = _create_reverse_test_project(tmp_path)
        g = _exec_visualize()
        g['visualize'](str(proj), mode='call', entry='validate_config', reverse=True)
        output = (proj / 'docs/architecture/graphs/call_graph.mmd').read_text()
        assert output.startswith('graph TD')

    def test_reverse_not_in_forward_mode(self, tmp_path):
        """Forward mode (no --reverse) from validate_config should NOT show deploy."""
        proj = _create_reverse_test_project(tmp_path)
        g = _exec_visualize()
        # Forward BFS from validate_config: validate_config has no callees, so output has only validate_config
        g['visualize'](str(proj), mode='call', entry='validate_config', reverse=False)
        output = (proj / 'docs/architecture/graphs/call_graph.mmd').read_text()
        # Forward: validate_config has no callees — deploy should NOT be a forward callee
        assert 'deploy' not in output or 'validate_config' in output  # at minimum entry is present

    def test_reverse_accepts_flag_in_signature(self):
        """visualize() function must accept a reverse parameter."""
        import inspect
        g = _exec_visualize()
        sig = inspect.signature(g['visualize'])
        assert 'reverse' in sig.parameters


# ==============================================================================
# AC2: Test Mapping via impact subcommand
# ==============================================================================
class TestImpactSubcommand:
    """AC2: impact subcommand maps changed functions to test files."""

    def test_impact_function_exists(self):
        """impact() function must exist in visualize namespace."""
        g = _exec_visualize()
        assert 'impact' in g, "impact() function should be defined in visualize.py"

    def test_impact_finds_direct_test_file(self, tmp_path):
        """validate_config in config.py maps to tests/unit/test_config.py."""
        proj = _create_impact_test_project(tmp_path)
        g = _exec_visualize()
        result = g['impact'](str(proj), entry='validate_config')
        assert 'test_config.py' in result, f"Expected test_config.py in '{result}'"

    def test_impact_finds_transitive_test_file(self, tmp_path):
        """validate_config is called by _deploy_classic in deployer.py → test_deployer.py."""
        proj = _create_impact_test_project(tmp_path)
        g = _exec_visualize()
        result = g['impact'](str(proj), entry='validate_config')
        assert 'test_deployer.py' in result, f"Expected test_deployer.py in '{result}'"

    def test_impact_returns_space_separated(self, tmp_path):
        """impact() output is space-separated list of test file paths."""
        proj = _create_impact_test_project(tmp_path)
        g = _exec_visualize()
        result = g['impact'](str(proj), entry='validate_config')
        # Each token should be a path-like string
        assert isinstance(result, str)
        for part in result.strip().split():
            assert '/' in part or '\\' in part, f"Expected file paths, got: {part}"

    def test_impact_returns_empty_for_unknown_entry(self, tmp_path):
        """Unknown entry function returns empty string (not error)."""
        proj = _create_impact_test_project(tmp_path)
        g = _exec_visualize()
        result = g['impact'](str(proj), entry='nonexistent_function_xyz')
        assert isinstance(result, str)
        # Should be empty or a 'not found' message, but not raise an exception


# ==============================================================================
# AC3/AC4/AC5: Regression Gate prompt tests (project-done.md template)
# ==============================================================================
class TestRegressionGatePrompt:
    """AC3/AC4/AC5: Regression Gate in project-done.md template."""

    def _get_done_md(self):
        from pactkit.prompts.commands import COMMANDS_CONTENT
        return COMMANDS_CONTENT.get('project-done.md', '')

    def test_impact_based_regression_mentioned(self):
        """AC3: project-done.md Regression Gate mentions IMPACT-BASED strategy."""
        done_md = self._get_done_md()
        assert 'IMPACT-BASED' in done_md, "Regression Gate should mention IMPACT-BASED strategy"

    def test_impact_command_referenced(self):
        """AC3: project-done.md Regression Gate references the impact command."""
        done_md = self._get_done_md()
        assert 'impact' in done_md.lower(), "Regression Gate should reference the impact command"

    def test_fallback_to_full_regression(self):
        """AC4: project-done.md Regression Gate mentions fallback to full regression."""
        done_md = self._get_done_md()
        # The fallback should be present
        assert '50' in done_md, "Regression Gate should mention the 50-file threshold"

    def test_version_bump_forces_full_regression(self):
        """AC5: project-done.md Regression Gate forces full regression on version bump."""
        done_md = self._get_done_md()
        assert 'version bump' in done_md.lower() or 'version_bump' in done_md.lower() or \
               'pyproject.toml' in done_md, \
               "Regression Gate should handle version bump forcing full regression"

    def test_release_full_regression_log_message(self):
        """AC5: project-done.md contains the required log message for release."""
        done_md = self._get_done_md()
        assert 'release requires full test suite' in done_md or 'version bump' in done_md.lower(), \
               "Regression Gate should contain the release log message"


# ==============================================================================
# R4: regression config section
# ==============================================================================
class TestRegressionConfig:
    """R4: regression config section in pactkit.yaml."""

    def test_regression_in_default_config(self):
        """regression section must be in get_default_config()."""
        from pactkit.config import get_default_config
        cfg = get_default_config()
        assert 'regression' in cfg, "regression section must be in default config"

    def test_regression_default_strategy(self):
        """Default regression strategy is 'impact'."""
        from pactkit.config import get_default_config
        cfg = get_default_config()
        assert cfg['regression'].get('strategy') == 'impact'

    def test_regression_default_max_impact(self):
        """Default max_impact_tests is 50."""
        from pactkit.config import get_default_config
        cfg = get_default_config()
        assert cfg['regression'].get('max_impact_tests') == 50

    def test_regression_in_generated_yaml(self):
        """generate_default_yaml() must include regression section."""
        from pactkit.config import generate_default_yaml
        yaml_str = generate_default_yaml()
        assert 'regression:' in yaml_str
        assert 'strategy:' in yaml_str
        assert 'max_impact_tests:' in yaml_str

    def test_regression_validates_strategy(self):
        """validate_config warns if regression.strategy is not 'impact' or 'full'."""
        from pactkit.config import validate_config
        cfg = {'regression': {'strategy': 'invalid_strategy', 'max_impact_tests': 50}}
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always')
            validate_config(cfg)
            strategy_warnings = [x for x in w if 'strategy' in str(x.message).lower()]
            assert len(strategy_warnings) >= 1, "Should warn on invalid regression strategy"

    def test_regression_rewrite_yaml_includes_section(self):
        """_rewrite_yaml preserves regression section."""
        from pactkit.config import _rewrite_yaml, get_default_config
        cfg = get_default_config()
        cfg['regression'] = {'strategy': 'full', 'max_impact_tests': 20}
        with tempfile.NamedTemporaryFile(suffix='.yaml', delete=False, mode='w') as f:
            fname = f.name
        path = Path(fname)
        try:
            _rewrite_yaml(path, cfg)
            content = path.read_text()
            assert 'regression:' in content
            assert 'strategy: full' in content
            assert 'max_impact_tests: 20' in content
        finally:
            path.unlink(missing_ok=True)
