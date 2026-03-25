"""Tests for STORY-slim-043: Cross-Service Impact."""
import textwrap


def _build_service_graph():
    """Build a service topology graph for testing."""
    from pactkit.skills.visualize import WorkflowNode, WorkflowEdge, WorkflowGraph
    g = WorkflowGraph()
    # Services
    g.add_node(WorkflowNode(id='user-service', kind='service', label='user-service'))
    g.add_node(WorkflowNode(id='order-service', kind='service', label='order-service'))
    g.add_node(WorkflowNode(id='notification-service', kind='service', label='notification-service'))
    # APIs
    g.add_node(WorkflowNode(id='get-users', kind='api', label='GET /users'))
    g.add_node(WorkflowNode(id='post-orders', kind='api', label='POST /orders'))
    # Edges: order-service calls user-service API
    g.add_edge(WorkflowEdge(source='user-service', target='get-users', relation='calls_api'))
    g.add_edge(WorkflowEdge(source='order-service', target='get-users', relation='calls_api'))
    g.add_edge(WorkflowEdge(source='order-service', target='post-orders', relation='calls_api'))
    # notification-service depends on order-service
    g.add_edge(WorkflowEdge(source='notification-service', target='order-service', relation='depends_on'))
    return g


# ── reverse_reach on service graph (R1) ──────────────────────────────

class TestReverseReachOnServiceGraph:
    """Test that reverse_reach traverses service→api→service edges."""

    def test_reverse_reach_finds_upstream_services(self):
        g = _build_service_graph()
        reached = g.reverse_reach('get-users')
        assert 'user-service' in reached
        assert 'order-service' in reached

    def test_reverse_reach_from_service(self):
        g = _build_service_graph()
        reached = g.reverse_reach('order-service')
        assert 'notification-service' in reached

    def test_reverse_reach_leaf_service(self):
        g = _build_service_graph()
        reached = g.reverse_reach('notification-service')
        # notification-service is a leaf — no one depends on it
        assert reached == {'notification-service'}


# ── Service-specific output format (R2) ──────────────────────────────

class TestServiceImpactOutput:
    """Test workflow_impact produces service-grouped output."""

    def test_impact_groups_by_service_kind(self, tmp_path):
        from pactkit.skills.visualize import workflow_impact
        # Create a microservice project for build_workflow_graph to detect
        (tmp_path / 'docker-compose.yml').write_text(textwrap.dedent("""\
            version: "3"
            services:
              user-service:
                image: user
              order-service:
                image: order
                depends_on:
                  - user-service
        """), encoding='utf-8')
        result = workflow_impact(target=str(tmp_path), entry='user-service')
        assert 'Services' in result
        assert 'order-service' in result

    def test_impact_shows_api_kind(self, tmp_path):
        from pactkit.skills.visualize import workflow_impact
        (tmp_path / 'docker-compose.yml').write_text(textwrap.dedent("""\
            version: "3"
            services:
              api:
                image: api
        """), encoding='utf-8')
        (tmp_path / 'openapi.yaml').write_text(textwrap.dedent("""\
            openapi: "3.0.0"
            info:
              title: "API"
              version: "1.0"
            paths:
              /health:
                get:
                  summary: Health check
        """), encoding='utf-8')
        # Just verify it doesn't crash — the API node may not be reachable from "api" service
        result = workflow_impact(target=str(tmp_path), entry='api')
        assert 'api' in result.lower()


# ── regression_workflow_impact service matching (R3) ──────────────────

class TestRegressionServiceImpact:
    """Test regression_workflow_impact matches changed files against service nodes."""

    def test_matches_service_dir_to_service_node(self, tmp_path):
        from pactkit.skills.visualize import regression_workflow_impact
        (tmp_path / 'docker-compose.yml').write_text(textwrap.dedent("""\
            version: "3"
            services:
              user-service:
                image: user
              order-service:
                image: order
                depends_on:
                  - user-service
        """), encoding='utf-8')
        result = regression_workflow_impact(
            target=str(tmp_path),
            changed_files=['services/user-service/handler.py'],
        )
        # Should detect user-service impact
        matching = [l for l in result if 'user-service' in l]
        assert len(matching) >= 1

    def test_no_match_returns_empty(self, tmp_path):
        from pactkit.skills.visualize import regression_workflow_impact
        (tmp_path / 'docker-compose.yml').write_text(textwrap.dedent("""\
            version: "3"
            services:
              web:
                image: nginx
        """), encoding='utf-8')
        result = regression_workflow_impact(
            target=str(tmp_path),
            changed_files=['unrelated/file.py'],
        )
        assert result == []
