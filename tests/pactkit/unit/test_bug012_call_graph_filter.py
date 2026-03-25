"""Tests for BUG-012: Call graph noise filter — remove builtins and local method calls."""
import sys
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


def _create_noisy_project(tmp_path):
    """Create a project with builtins, local method calls, and project-internal calls."""
    src = tmp_path / 'src'
    src.mkdir()
    (src / '__init__.py').write_text('', encoding='utf-8')

    # Module with a mix of builtin calls, local method calls, and project-internal calls
    (src / 'core.py').write_text(
        'def load_config():\n'
        '    data = {}\n'
        '    items = list(data.keys())\n'      # list() = builtin, data.keys() = local method
        '    length = len(items)\n'             # len() = builtin
        '    filtered = sorted(items)\n'        # sorted() = builtin
        '    return filtered\n'
        '\n'
        'def process():\n'
        '    cfg = load_config()\n'             # project-internal call
        '    result = transform(cfg)\n'         # project-internal call
        '    if isinstance(cfg, dict):\n'       # isinstance() = builtin
        '        print("ok")\n'                 # print() = builtin
        '    return result\n'
        '\n'
        'def transform(data):\n'
        '    lines = []\n'
        '    lines.append("header")\n'          # lines.append = local method call
        '    content = data.get("key", "")\n'   # data.get = local method call
        '    path = Path(".")\n'                # Path() = not a builtin, but not project
        '    if path.exists():\n'               # path.exists = local method call
        '        pass\n'
        '    return lines\n',
        encoding='utf-8'
    )

    # Module with self.method() calls
    (src / 'models.py').write_text(
        'class Engine:\n'
        '    def run(self):\n'
        '        result = self.prepare()\n'     # self.method -> Engine.prepare
        '        return result\n'
        '\n'
        '    def prepare(self):\n'
        '        return "ready"\n',
        encoding='utf-8'
    )

    # Module that calls across modules
    (src / 'main.py').write_text(
        'from src.core import process\n'
        '\n'
        'def deploy():\n'
        '    result = process()\n'              # project-internal
        '    return result\n',
        encoding='utf-8'
    )

    return tmp_path


# ==============================================================================
# AC1: Builtins filtered from call graph
# ==============================================================================
class TestBuiltinsFiltered:
    """Given PactKit source with calls to isinstance, len, sorted, etc.
    When visualize --mode call is run
    Then the call_graph.mmd does NOT contain nodes for builtin functions."""

    BUILTINS = [
        'isinstance', 'len', 'sorted', 'set', 'dict', 'type', 'print',
        'any', 'str', 'int', 'float', 'bool', 'list', 'tuple', 'range',
        'enumerate', 'zip', 'map', 'filter', 'super', 'hasattr', 'getattr',
        'setattr', 'repr', 'min', 'max', 'abs', 'round', 'open',
        'ValueError', 'TypeError', 'KeyError',
    ]

    def test_no_builtin_nodes_in_call_graph(self, tmp_path):
        proj = _create_noisy_project(tmp_path)
        g = _exec_visualize()
        g['visualize'](str(proj), mode='call')
        output = (proj / 'docs/architecture/graphs/call_graph.mmd').read_text()
        for builtin in self.BUILTINS:
            # Check that builtin doesn't appear as a standalone node name
            # Node format: `    builtin_name["builtin_name"]`
            assert f'["{builtin}"]' not in output, \
                f'Builtin "{builtin}" should be filtered from call graph'

    def test_no_builtin_edges_in_call_graph(self, tmp_path):
        proj = _create_noisy_project(tmp_path)
        g = _exec_visualize()
        g['visualize'](str(proj), mode='call')
        output = (proj / 'docs/architecture/graphs/call_graph.mmd').read_text()
        lines = output.strip().split('\n')
        edge_lines = [l for l in lines if '-->' in l]
        for edge in edge_lines:
            # Neither side of the edge should be a pure builtin
            parts = edge.strip().split('-->')
            src_label = parts[0].strip()
            dst_label = parts[1].strip()
            for builtin in self.BUILTINS:
                assert src_label != builtin and dst_label != builtin, \
                    f'Edge references builtin "{builtin}": {edge.strip()}'


# ==============================================================================
# AC2: Local method calls filtered
# ==============================================================================
class TestLocalMethodCallsFiltered:
    """Given code like lines.append(...), data.get(...), path.exists()
    When visualize --mode call is run
    Then these do NOT appear as nodes in call_graph.mmd."""

    LOCAL_METHODS = [
        'lines.append', 'data.get', 'path.exists',
        'content.append', 'content.extend', 'content.replace',
    ]

    def test_no_local_method_nodes(self, tmp_path):
        proj = _create_noisy_project(tmp_path)
        g = _exec_visualize()
        g['visualize'](str(proj), mode='call')
        output = (proj / 'docs/architecture/graphs/call_graph.mmd').read_text()
        for method in self.LOCAL_METHODS:
            safe_name = method.replace('.', '_')
            assert f'["{method}"]' not in output, \
                f'Local method call "{method}" should be filtered'
            # Also check the safe (underscore) form used in node IDs
            assert f'{safe_name}[' not in output, \
                f'Local method call node "{safe_name}" should be filtered'


# ==============================================================================
# AC3: Project-internal calls preserved
# ==============================================================================
class TestProjectInternalCallsPreserved:
    """Given code calling _deploy_agents(...), atomic_write(...), load_config(...)
    When visualize --mode call is run
    Then these appear as edges in call_graph.mmd."""

    def test_project_internal_calls_present(self, tmp_path):
        proj = _create_noisy_project(tmp_path)
        g = _exec_visualize()
        g['visualize'](str(proj), mode='call')
        output = (proj / 'docs/architecture/graphs/call_graph.mmd').read_text()
        # process() calls load_config() and transform() — both project-internal
        assert 'process' in output, 'Project function "process" should be in call graph'
        assert 'load_config' in output, 'Project function "load_config" should be in call graph'
        assert 'transform' in output, 'Project function "transform" should be in call graph'

    def test_cross_module_calls_present(self, tmp_path):
        proj = _create_noisy_project(tmp_path)
        g = _exec_visualize()
        g['visualize'](str(proj), mode='call')
        output = (proj / 'docs/architecture/graphs/call_graph.mmd').read_text()
        # deploy() calls process() — cross-module project call
        assert 'deploy' in output, 'Project function "deploy" should be in call graph'
        edge_lines = [l for l in output.strip().split('\n') if '-->' in l]
        has_deploy_to_process = any('deploy' in l and 'process' in l for l in edge_lines)
        assert has_deploy_to_process, 'Edge deploy --> process should exist'

    def test_self_method_calls_preserved(self, tmp_path):
        """AC4: MUST retain calls to self.method() resolved to ClassName.method."""
        proj = _create_noisy_project(tmp_path)
        g = _exec_visualize()
        g['visualize'](str(proj), mode='call')
        output = (proj / 'docs/architecture/graphs/call_graph.mmd').read_text()
        # Engine.run() calls self.prepare() → should resolve to Engine.prepare
        assert 'Engine.run' in output or 'Engine_run' in output, \
            'Engine.run should be in call graph'
        assert 'Engine.prepare' in output or 'Engine_prepare' in output, \
            'Engine.prepare should be in call graph (self.method resolution)'


# ==============================================================================
# AC4: Entry-point tracing still works
# ==============================================================================
class TestEntryPointTracing:
    """Given visualize --mode call --entry deploy
    When BFS traversal runs from deploy function
    Then the transitive call chain shows only project-internal functions."""

    def test_entry_bfs_works(self, tmp_path):
        proj = _create_noisy_project(tmp_path)
        g = _exec_visualize()
        g['visualize'](str(proj), mode='call', entry='deploy')
        output = (proj / 'docs/architecture/graphs/call_graph.mmd').read_text()
        # deploy → process → load_config, transform
        assert 'deploy' in output
        assert 'process' in output
        assert 'load_config' in output
        assert 'transform' in output

    def test_entry_bfs_no_builtins(self, tmp_path):
        proj = _create_noisy_project(tmp_path)
        g = _exec_visualize()
        g['visualize'](str(proj), mode='call', entry='deploy')
        output = (proj / 'docs/architecture/graphs/call_graph.mmd').read_text()
        # BFS chain should not include builtins like isinstance, len, sorted, print
        for builtin in ['isinstance', 'len', 'sorted', 'print']:
            assert f'["{builtin}"]' not in output, \
                f'BFS entry chain should not include builtin "{builtin}"'

    def test_entry_bfs_no_local_methods(self, tmp_path):
        proj = _create_noisy_project(tmp_path)
        g = _exec_visualize()
        g['visualize'](str(proj), mode='call', entry='process')
        output = (proj / 'docs/architecture/graphs/call_graph.mmd').read_text()
        # BFS from process should not include lines.append, data.get
        for method in ['lines.append', 'data.get', 'path.exists']:
            safe = method.replace('.', '_')
            assert f'["{method}"]' not in output, \
                f'BFS entry chain should not include local method "{method}"'


# ==============================================================================
# AC5: Significant noise reduction
# ==============================================================================
class TestNoiseReduction:
    """Given the current 464-line call_graph.mmd
    When BUG-012 fix is applied
    Then the call graph has meaningfully fewer nodes."""

    def test_func_registry_edge_filter(self, tmp_path):
        """SHOULD only include edges where at least one endpoint is in func_registry."""
        proj = _create_noisy_project(tmp_path)
        g = _exec_visualize()
        g['visualize'](str(proj), mode='call')
        output = (proj / 'docs/architecture/graphs/call_graph.mmd').read_text()
        lines = output.strip().split('\n')
        # With filtering, the graph should be compact
        # Our test project has ~8 project functions (load_config, process, transform,
        # deploy, Engine.run, Engine.prepare) — graph should be well under 50 lines
        assert len(lines) < 50, \
            f'Call graph should be compact, got {len(lines)} lines'

    def test_only_project_functions_as_nodes(self, tmp_path):
        """After filtering, every node in the graph should be a project-defined function."""
        proj = _create_noisy_project(tmp_path)
        g = _exec_visualize()
        g['visualize'](str(proj), mode='call')
        output = (proj / 'docs/architecture/graphs/call_graph.mmd').read_text()
        lines = output.strip().split('\n')
        # Extract node labels from lines like: `    name["label"]`
        node_labels = []
        for line in lines:
            if '["' in line and '-->' not in line:
                label = line.split('["')[1].split('"]')[0]
                node_labels.append(label)
        # All node labels should be project functions
        project_funcs = {
            'load_config', 'process', 'transform', 'deploy',
            'Engine.run', 'Engine.prepare',
        }
        for label in node_labels:
            assert label in project_funcs, \
                f'Non-project node "{label}" found in filtered call graph'
