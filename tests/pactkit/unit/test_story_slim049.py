"""Tests for STORY-slim-049: Split unified graph — full for AI + focused sub-graphs for humans."""
import sys
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))
from pactkit.skills.visualize import (
    MAX_WORKFLOW_NODES,
    WorkflowEdge,
    WorkflowGraph,
    WorkflowNode,
    build_unified_graph,
    export_focus_graphs,
)


def _make_project(tmp_path, files: dict[str, str]) -> Path:
    for rel, content in files.items():
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding='utf-8')
    return tmp_path


# --- R1: No truncation in build_unified_graph ---

class TestNoTruncation:
    def test_full_graph_no_truncation_warning(self, tmp_path):
        """AC1: build_unified_graph returns all nodes without truncation warning."""
        # Create a project with 600+ functions (exceeding MAX_WORKFLOW_NODES)
        funcs = '\n'.join(f'def func_{i}(): pass' for i in range(600))
        _make_project(tmp_path, {
            'pyproject.toml': '[project]\nname = "bigproject"',
            'src/big.py': funcs,
        })
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always')
            graph = build_unified_graph(str(tmp_path))
            truncation_warnings = [x for x in w if 'truncating' in str(x.message).lower()]
            assert len(truncation_warnings) == 0, f'Unexpected truncation warning: {truncation_warnings}'
        # All 600 function nodes should be present
        func_nodes = [n for n in graph.nodes.values() if n.kind == 'function']
        assert len(func_nodes) >= 600

    def test_max_workflow_nodes_constant_still_defined(self):
        """R5: MAX_WORKFLOW_NODES constant still exists for backward compat."""
        assert isinstance(MAX_WORKFLOW_NODES, int)
        assert MAX_WORKFLOW_NODES == 500


# --- R2: export_focus_graphs ---

class TestExportFocusGraphs:
    def _build_graph_with_entries(self) -> WorkflowGraph:
        """Build a graph with commands, services, and pages as entry points."""
        g = WorkflowGraph()
        g.layered = True
        # Commands
        g.add_node(WorkflowNode(id='project-act', kind='command', label='project-act'))
        g.add_node(WorkflowNode(id='project-plan', kind='command', label='project-plan'))
        # Services
        g.add_node(WorkflowNode(id='order-svc', kind='service', label='order-svc'))
        # Pages
        g.add_node(WorkflowNode(id='/dashboard', kind='page', label='/dashboard'))
        # Supporting nodes
        g.add_node(WorkflowNode(id='senior-dev', kind='agent', label='Senior Developer'))
        g.add_node(WorkflowNode(id='pactkit-board', kind='skill', label='pactkit-board'))
        # Edges
        g.add_edge(WorkflowEdge(source='project-act', target='senior-dev', relation='invokes'))
        g.add_edge(WorkflowEdge(source='project-act', target='pactkit-board', relation='depends_on'))
        g.add_edge(WorkflowEdge(source='project-plan', target='senior-dev', relation='invokes'))
        return g

    def test_creates_files_per_entry_point(self, tmp_path):
        """AC2: One .mmd file per entry point (command, service, page)."""
        graph = self._build_graph_with_entries()
        result = export_focus_graphs(graph, tmp_path)
        assert isinstance(result, list)
        # 4 entry points: project-act, project-plan, order-svc, /dashboard
        assert len(result) == 4
        for p in result:
            assert p.exists()
            assert p.suffix == '.mmd'

    def test_focus_file_starts_with_graph_td(self, tmp_path):
        """AC3: Each focused sub-graph is valid Mermaid starting with 'graph TD'."""
        graph = self._build_graph_with_entries()
        result = export_focus_graphs(graph, tmp_path)
        for p in result:
            content = p.read_text(encoding='utf-8')
            assert content.startswith('graph TD'), f'{p.name} does not start with graph TD'

    def test_focus_graph_contains_only_reachable_nodes(self, tmp_path):
        """AC2: Each focus file contains only nodes reachable via reverse_reach."""
        graph = self._build_graph_with_entries()
        export_focus_graphs(graph, tmp_path)
        # Find the project-act focus file
        act_files = list(tmp_path.glob('focus_project_act*'))
        assert len(act_files) == 1
        content = act_files[0].read_text(encoding='utf-8')
        # project-act's reverse_reach should include senior-dev and pactkit-board
        assert 'senior_dev' in content or 'senior-dev' in content
        assert 'pactkit_board' in content or 'pactkit-board' in content
        # order-svc should NOT be in project-act's focus graph
        assert 'order_svc' not in content and 'order-svc' not in content

    def test_empty_graph_returns_empty_list(self, tmp_path):
        """Edge case: graph with no entry points produces no files."""
        graph = WorkflowGraph()
        graph.add_node(WorkflowNode(id='some-func', kind='function', label='some_func'))
        result = export_focus_graphs(graph, tmp_path)
        assert result == []

    def test_output_dir_created_if_missing(self, tmp_path):
        """export_focus_graphs creates output_dir if it doesn't exist."""
        graph = self._build_graph_with_entries()
        out = tmp_path / 'nested' / 'focus'
        result = export_focus_graphs(graph, out)
        assert out.is_dir()
        assert len(result) > 0


# --- R3: max_render_nodes in to_mermaid ---

class TestMaxRenderNodes:
    def test_default_renders_all(self):
        """Default max_render_nodes=0 renders all nodes."""
        g = WorkflowGraph()
        for i in range(100):
            g.add_node(WorkflowNode(id=f'n{i}', kind='function', label=f'n{i}'))
        mermaid = g.to_mermaid()
        # Should have all 100 nodes
        node_lines = [l for l in mermaid.split('\n') if '[' in l and 'NOTE' not in l]
        assert len(node_lines) == 100

    def test_truncates_at_limit(self):
        """AC4: max_render_nodes=50 renders 50 nodes + NOTE."""
        g = WorkflowGraph()
        for i in range(100):
            g.add_node(WorkflowNode(id=f'n{i}', kind='function', label=f'n{i}'))
        mermaid = g.to_mermaid(max_render_nodes=50)
        node_lines = [l for l in mermaid.split('\n') if '[' in l and 'NOTE' not in l]
        assert len(node_lines) == 50
        assert 'NOTE' in mermaid
        assert '50 more' in mermaid

    def test_no_truncation_when_under_limit(self):
        """When graph has fewer nodes than limit, no NOTE added."""
        g = WorkflowGraph()
        for i in range(10):
            g.add_node(WorkflowNode(id=f'n{i}', kind='function', label=f'n{i}'))
        mermaid = g.to_mermaid(max_render_nodes=50)
        assert 'NOTE' not in mermaid


# --- R4: CLI unified mode ---

class TestUnifiedCLI:
    def test_unified_mode_writes_unified_graph(self, tmp_path):
        """AC5: visualize --mode unified writes unified_graph.mmd."""
        from pactkit.skills.visualize import visualize
        _make_project(tmp_path, {
            'pyproject.toml': '[project]\nname = "test"',
            'src/app.py': 'def main(): pass\n',
        })
        result = visualize(target=str(tmp_path), mode='unified')
        expected = tmp_path / 'docs' / 'architecture' / 'graphs' / 'unified_graph.mmd'
        assert expected.exists()
        content = expected.read_text(encoding='utf-8')
        assert content.startswith('graph TD')

    def test_unified_split_creates_focus_dir(self, tmp_path):
        """AC6: --split generates focus/ directory with per-entry-point files."""
        from pactkit.skills.visualize import visualize
        _make_project(tmp_path, {
            'pyproject.toml': '[project]\nname = "test"',
            '.claude/commands/project-act.md': '# Act\n- **Agent**: Senior Developer\n',
            'src/app.py': 'def main(): pass\n',
        })
        result = visualize(target=str(tmp_path), mode='unified', split=True)
        focus_dir = tmp_path / 'docs' / 'architecture' / 'graphs' / 'focus'
        assert focus_dir.is_dir()
        focus_files = list(focus_dir.glob('*.mmd'))
        assert len(focus_files) >= 1


# --- R5: Backward compatibility ---

class TestBackwardCompat:
    def test_workflow_mode_unchanged(self, tmp_path):
        """AC7: workflow mode still works identically."""
        from pactkit.skills.visualize import visualize
        _make_project(tmp_path, {
            'pyproject.toml': '[project]\nname = "test"',
            '.claude/commands/project-act.md': '# Act\n- **Agent**: Senior Developer\n',
        })
        result = visualize(target=str(tmp_path), mode='workflow')
        expected = tmp_path / 'docs' / 'architecture' / 'graphs' / 'workflow_graph.mmd'
        assert expected.exists()
        assert 'unified_graph' not in result
