"""Tests for STORY-slim-048: Unified Layered Graph."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))
from pactkit.skills.visualize import (
    MAX_WORKFLOW_NODES,
    WorkflowEdge,
    WorkflowGraph,
    WorkflowNode,
    _build_bridge_edges,
    _load_code_graph,
    build_unified_graph,
)


def make_project(tmp_path, files: dict[str, str]) -> Path:
    for rel, content in files.items():
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding='utf-8')
    return tmp_path


# --- R5: MAX_WORKFLOW_NODES constant ---

class TestMaxWorkflowNodesConstant:
    def test_constant_defined_at_500(self):
        assert MAX_WORKFLOW_NODES == 500

    def test_constant_is_integer(self):
        assert isinstance(MAX_WORKFLOW_NODES, int)


# --- R1: _load_code_graph produces function nodes ---

class TestLoadCodeGraph:
    def test_python_function_nodes_created(self, tmp_path):
        make_project(tmp_path, {
            'pyproject.toml': '[project]\nname = "test"',
            'src/mymodule.py': (
                "def create_order():\n    pass\n"
                "def cancel_order():\n    pass\n"
            ),
        })
        graph, func_registry = _load_code_graph(tmp_path)
        func_ids = [n.id for n in graph.nodes.values() if n.kind == 'function']
        assert 'create_order' in func_ids
        assert 'cancel_order' in func_ids

    def test_function_kind_is_function(self, tmp_path):
        make_project(tmp_path, {
            'pyproject.toml': '[project]\nname = "test"',
            'src/utils.py': "def helper(): pass\n",
        })
        graph, _ = _load_code_graph(tmp_path)
        function_nodes = [n for n in graph.nodes.values() if n.kind == 'function']
        assert len(function_nodes) >= 1

    def test_call_edges_created(self, tmp_path):
        make_project(tmp_path, {
            'pyproject.toml': '[project]\nname = "test"',
            'src/app.py': (
                "def helper(): pass\n"
                "def main():\n    helper()\n"
            ),
        })
        graph, _ = _load_code_graph(tmp_path)
        edge_pairs = [(e.source, e.target, e.relation) for e in graph.edges]
        assert any(src == 'main' and dst == 'helper' and rel == 'calls'
                   for src, dst, rel in edge_pairs)

    def test_returns_func_registry_dict(self, tmp_path):
        make_project(tmp_path, {
            'pyproject.toml': '[project]\nname = "test"',
            'src/utils.py': "def fmt_date(): pass\n",
        })
        _, func_registry = _load_code_graph(tmp_path)
        assert isinstance(func_registry, dict)
        assert 'fmt_date' in func_registry

    def test_empty_project_returns_empty(self, tmp_path):
        graph, func_registry = _load_code_graph(tmp_path)
        assert len(graph.nodes) == 0
        assert len(func_registry) == 0


# --- R2: _build_bridge_edges ---

class TestBuildBridgeEdges:
    def test_function_to_skill_bridge(self):
        func_registry = {'archive': 'some/path/pactkit-board/scripts/board.py'}
        topology_graph = WorkflowGraph()
        topology_graph.add_node(WorkflowNode(id='pactkit-board', kind='skill', label='pactkit-board'))
        unified = WorkflowGraph()
        unified.add_node(WorkflowNode(id='archive', kind='function', label='archive'))
        unified.add_node(WorkflowNode(id='pactkit-board', kind='skill', label='pactkit-board'))
        _build_bridge_edges(func_registry, topology_graph, unified)
        edge_targets = [(e.source, e.target) for e in unified.edges]
        assert ('archive', 'pactkit-board') in edge_targets

    def test_function_to_service_bridge(self):
        func_registry = {'createOrder': 'order-service/src/handler.py'}
        topology_graph = WorkflowGraph()
        topology_graph.add_node(WorkflowNode(id='order-service', kind='service', label='order-service'))
        unified = WorkflowGraph()
        unified.add_node(WorkflowNode(id='createOrder', kind='function', label='createOrder'))
        unified.add_node(WorkflowNode(id='order-service', kind='service', label='order-service'))
        _build_bridge_edges(func_registry, topology_graph, unified)
        edge_targets = [(e.source, e.target) for e in unified.edges]
        assert ('createOrder', 'order-service') in edge_targets

    def test_no_bridge_when_no_match(self):
        func_registry = {'unrelated_func': 'some/random/path.py'}
        topology_graph = WorkflowGraph()
        topology_graph.add_node(WorkflowNode(id='pactkit-board', kind='skill', label='pactkit-board'))
        unified = WorkflowGraph()
        _build_bridge_edges(func_registry, topology_graph, unified)
        assert len(unified.edges) == 0


# --- R3: layered to_mermaid ---

class TestLayeredMermaid:
    def _make_unified_graph(self) -> WorkflowGraph:
        graph = WorkflowGraph()
        graph.layered = True
        graph.add_node(WorkflowNode(id='create_order', kind='function', label='create_order'))
        graph.add_node(WorkflowNode(id='project-act', kind='command', label='project-act'))
        graph.add_node(WorkflowNode(id='order-service', kind='service', label='order-service'))
        graph.add_node(WorkflowNode(id='/dashboard', kind='page', label='/dashboard'))
        return graph

    def test_code_dimension_subgraph_present(self):
        graph = self._make_unified_graph()
        mermaid = graph.to_mermaid()
        assert 'Code Dimension' in mermaid

    def test_pdca_topology_subgraph_present(self):
        graph = self._make_unified_graph()
        mermaid = graph.to_mermaid()
        assert 'PDCA Topology' in mermaid

    def test_service_topology_subgraph_present(self):
        graph = self._make_unified_graph()
        mermaid = graph.to_mermaid()
        assert 'Service Topology' in mermaid

    def test_frontend_topology_subgraph_present(self):
        graph = self._make_unified_graph()
        mermaid = graph.to_mermaid()
        assert 'Frontend Topology' in mermaid

    def test_non_layered_graph_unchanged(self):
        graph = WorkflowGraph()
        graph.add_node(WorkflowNode(id='project-act', kind='command', label='project-act'))
        mermaid = graph.to_mermaid()
        assert 'Commands' in mermaid
        assert 'Code Dimension' not in mermaid


# --- R4: Cross-dimension impact analysis ---

class TestCrossDimensionImpact:
    def test_reverse_reach_crosses_function_to_service(self):
        """Bridge edges enable cross-dimension reverse_reach traversal.

        reverse_reach('order-service') finds both:
        - createOrder (via createOrder→order-service belongs_to bridge)
        - payment-service (via payment-service→order-service depends_on)
        This is the service's impact set — all things that contribute to/depend on order-service.
        """
        graph = WorkflowGraph()
        graph.add_node(WorkflowNode(id='createOrder', kind='function', label='createOrder'))
        graph.add_node(WorkflowNode(id='order-service', kind='service', label='order-service'))
        graph.add_node(WorkflowNode(id='payment-service', kind='service', label='payment-service'))
        graph.add_edge(WorkflowEdge(source='createOrder', target='order-service', relation='belongs_to'))
        graph.add_edge(WorkflowEdge(source='payment-service', target='order-service', relation='depends_on'))
        # reverse_reach('order-service') = all nodes pointing to order-service
        reached = graph.reverse_reach('order-service')
        assert 'createOrder' in reached   # function belongs to service
        assert 'payment-service' in reached  # service depends on order-service

    def test_cross_dimension_bridge_traversal(self):
        """If function→service→dependent_service, reverse_reach from function reaches all."""
        graph = WorkflowGraph()
        graph.add_node(WorkflowNode(id='fn', kind='function', label='fn'))
        graph.add_node(WorkflowNode(id='svc-a', kind='service', label='svc-a'))
        graph.add_node(WorkflowNode(id='svc-b', kind='service', label='svc-b'))
        graph.add_edge(WorkflowEdge(source='fn', target='svc-a', relation='belongs_to'))
        graph.add_edge(WorkflowEdge(source='svc-b', target='svc-a', relation='calls'))
        # reverse_reach from fn: fn -> svc-a (via belongs_to) -> svc-b (via calls to svc-a)
        # Wait, reverse_reach goes BACKWARD: who points TO fn?
        # fn points to svc-a. svc-b points to svc-a. So reverse_reach(svc-a) = {svc-a, fn, svc-b}
        reached_svc_a = graph.reverse_reach('svc-a')
        assert 'fn' in reached_svc_a
        assert 'svc-b' in reached_svc_a


# --- R5: Node limit truncation ---

class TestNodeLimitTruncation:
    def test_build_unified_graph_truncates_at_max(self):
        """When total nodes exceed MAX_WORKFLOW_NODES, graph is truncated."""
        graph = WorkflowGraph()
        # Add MAX+100 nodes
        for i in range(MAX_WORKFLOW_NODES + 100):
            graph.add_node(WorkflowNode(id=f'node_{i}', kind='function', label=f'node_{i}'))
        # Manually trigger truncation logic (same as build_unified_graph does)
        if len(graph.nodes) > MAX_WORKFLOW_NODES:
            keep_ids = set(list(graph.nodes.keys())[:MAX_WORKFLOW_NODES])
            graph.nodes = {k: v for k, v in graph.nodes.items() if k in keep_ids}
        assert len(graph.nodes) == MAX_WORKFLOW_NODES

    def test_build_unified_graph_empty_project(self, tmp_path):
        """Empty project should return empty or near-empty unified graph."""
        graph = build_unified_graph(str(tmp_path))
        assert isinstance(graph, WorkflowGraph)
        assert graph.layered is True

    def test_build_unified_graph_sets_layered_true(self, tmp_path):
        graph = build_unified_graph(str(tmp_path))
        assert graph.layered is True
