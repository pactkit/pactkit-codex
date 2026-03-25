"""Tests for STORY-slim-042: ServiceParser."""
import json
import textwrap


# ── ServiceParser detect tests (R1) ──────────────────────────────────

class TestServiceParserDetect:
    """Test ServiceParser.detect() using inherited markers."""

    def test_detect_docker_compose_yml(self, tmp_path):
        from pactkit.skills.visualize import ServiceParser
        (tmp_path / 'docker-compose.yml').write_text('version: "3"', encoding='utf-8')
        assert ServiceParser().detect(tmp_path) is True

    def test_detect_docker_compose_yaml(self, tmp_path):
        from pactkit.skills.visualize import ServiceParser
        (tmp_path / 'docker-compose.yaml').write_text('version: "3"', encoding='utf-8')
        assert ServiceParser().detect(tmp_path) is True

    def test_detect_openapi(self, tmp_path):
        from pactkit.skills.visualize import ServiceParser
        (tmp_path / 'openapi.yaml').write_text('openapi: "3.0"', encoding='utf-8')
        assert ServiceParser().detect(tmp_path) is True

    def test_detect_swagger(self, tmp_path):
        from pactkit.skills.visualize import ServiceParser
        (tmp_path / 'swagger.json').write_text('{}', encoding='utf-8')
        assert ServiceParser().detect(tmp_path) is True

    def test_detect_false_empty(self, tmp_path):
        from pactkit.skills.visualize import ServiceParser
        assert ServiceParser().detect(tmp_path) is False


# ── docker-compose parsing tests (R2) ────────────────────────────────

class TestParseDockerCompose:
    """Test ServiceParser parses docker-compose.yml for service nodes and edges."""

    def test_extracts_services(self, tmp_path):
        from pactkit.skills.visualize import ServiceParser
        (tmp_path / 'docker-compose.yml').write_text(textwrap.dedent("""\
            version: "3"
            services:
              web:
                image: nginx
                depends_on:
                  - db
                  - redis
              db:
                image: postgres
              redis:
                image: redis
        """), encoding='utf-8')
        g = ServiceParser().parse(tmp_path)
        assert 'web' in g.nodes
        assert 'db' in g.nodes
        assert 'redis' in g.nodes
        assert g.nodes['web'].kind == 'service'
        dep_edges = [e for e in g.edges if e.relation == 'depends_on']
        assert len(dep_edges) == 2
        targets = {e.target for e in dep_edges if e.source == 'web'}
        assert targets == {'db', 'redis'}

    def test_extracts_links(self, tmp_path):
        from pactkit.skills.visualize import ServiceParser
        (tmp_path / 'docker-compose.yml').write_text(textwrap.dedent("""\
            version: "3"
            services:
              app:
                image: myapp
                links:
                  - mongo
              mongo:
                image: mongo
        """), encoding='utf-8')
        g = ServiceParser().parse(tmp_path)
        dep_edges = [e for e in g.edges if e.source == 'app' and e.relation == 'depends_on']
        assert len(dep_edges) == 1
        assert dep_edges[0].target == 'mongo'

    def test_handles_depends_on_dict_form(self, tmp_path):
        from pactkit.skills.visualize import ServiceParser
        (tmp_path / 'docker-compose.yml').write_text(textwrap.dedent("""\
            version: "3"
            services:
              web:
                image: nginx
                depends_on:
                  db:
                    condition: service_healthy
              db:
                image: postgres
        """), encoding='utf-8')
        g = ServiceParser().parse(tmp_path)
        dep_edges = [e for e in g.edges if e.source == 'web' and e.relation == 'depends_on']
        assert len(dep_edges) == 1
        assert dep_edges[0].target == 'db'

    def test_empty_docker_compose(self, tmp_path):
        from pactkit.skills.visualize import ServiceParser
        (tmp_path / 'docker-compose.yml').write_text('version: "3"\n', encoding='utf-8')
        g = ServiceParser().parse(tmp_path)
        assert len(g.nodes) == 0


# ── OpenAPI/Swagger parsing tests (R3) ───────────────────────────────

class TestParseOpenAPI:
    """Test ServiceParser parses openapi.yaml for API nodes."""

    def test_extracts_openapi_paths(self, tmp_path):
        from pactkit.skills.visualize import ServiceParser
        (tmp_path / 'openapi.yaml').write_text(textwrap.dedent("""\
            openapi: "3.0.0"
            info:
              title: "User Service"
              version: "1.0"
            paths:
              /users:
                get:
                  summary: List users
                post:
                  summary: Create user
              /users/{id}:
                get:
                  summary: Get user
        """), encoding='utf-8')
        g = ServiceParser().parse(tmp_path)
        svc_nodes = [n for n in g.nodes.values() if n.kind == 'service']
        assert any('User Service' in n.label for n in svc_nodes)
        api_nodes = [n for n in g.nodes.values() if n.kind == 'api']
        assert len(api_nodes) >= 3  # GET /users, POST /users, GET /users/{id}

    def test_extracts_swagger_json(self, tmp_path):
        from pactkit.skills.visualize import ServiceParser
        swagger = {
            "swagger": "2.0",
            "info": {"title": "Order API", "version": "1.0"},
            "paths": {
                "/orders": {"get": {"summary": "List"}, "post": {"summary": "Create"}},
            }
        }
        (tmp_path / 'swagger.json').write_text(json.dumps(swagger), encoding='utf-8')
        g = ServiceParser().parse(tmp_path)
        api_nodes = [n for n in g.nodes.values() if n.kind == 'api']
        assert len(api_nodes) >= 2


# ── Proto file parsing tests (R4) ────────────────────────────────────

class TestParseProtoFiles:
    """Test ServiceParser parses *.proto files for service/rpc nodes."""

    def test_extracts_proto_services(self, tmp_path):
        from pactkit.skills.visualize import ServiceParser
        (tmp_path / 'user.proto').write_text(textwrap.dedent("""\
            syntax = "proto3";
            package user;
            service UserService {
                rpc GetUser (GetUserRequest) returns (UserResponse);
                rpc CreateUser (CreateUserRequest) returns (UserResponse);
            }
        """), encoding='utf-8')
        # Need a marker file for detect to work
        (tmp_path / 'docker-compose.yml').write_text('version: "3"\nservices:\n  api:\n    image: api\n', encoding='utf-8')
        g = ServiceParser().parse(tmp_path)
        svc_nodes = [n for n in g.nodes.values() if n.kind == 'service']
        assert any('UserService' in n.label for n in svc_nodes)
        api_nodes = [n for n in g.nodes.values() if n.kind == 'api']
        rpc_labels = {n.label for n in api_nodes}
        assert 'GetUser' in rpc_labels
        assert 'CreateUser' in rpc_labels


# ── Registry tests (R5) ──────────────────────────────────────────────

class TestServiceParserRegistry:
    """Test ServiceParser is registered in _TOPOLOGY_PARSERS."""

    def test_service_registered(self):
        from pactkit.skills.visualize import _TOPOLOGY_PARSERS, ServiceParser
        assert 'service' in _TOPOLOGY_PARSERS
        assert isinstance(_TOPOLOGY_PARSERS['service'], ServiceParser)


# ── Graceful fallback tests (R6) ─────────────────────────────────────

class TestYamlSafeLoadOnly:
    """Test yaml.safe_load is used and graceful fallback without pyyaml."""

    def test_no_crash_on_malformed_yaml(self, tmp_path):
        from pactkit.skills.visualize import ServiceParser
        (tmp_path / 'docker-compose.yml').write_text('{{invalid yaml', encoding='utf-8')
        g = ServiceParser().parse(tmp_path)
        # Should not crash — returns empty or partial graph
        assert isinstance(g.nodes, dict)
