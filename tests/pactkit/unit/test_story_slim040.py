"""Tests for STORY-slim-040: TopologyParser ABC + Auto-Detect."""


# ── TopologyParser ABC tests (R1) ────────────────────────────────────

class TestTopologyParserABC:
    """Test TopologyParser abstract base class."""

    def test_cannot_instantiate_directly(self):
        from pactkit.skills.visualize import TopologyParser
        import pytest
        with pytest.raises(TypeError):
            TopologyParser()

    def test_has_markers_class_attr(self):
        from pactkit.skills.visualize import TopologyParser
        assert hasattr(TopologyParser, 'markers')
        assert TopologyParser.markers == []

    def test_subclass_with_markers_detect_works(self, tmp_path):
        from pactkit.skills.visualize import TopologyParser, WorkflowGraph
        class TestParser(TopologyParser):
            markers = ['some-file.yml']
            def parse(self, root):
                return WorkflowGraph()
        (tmp_path / 'some-file.yml').write_text('test', encoding='utf-8')
        p = TestParser()
        assert p.detect(tmp_path) is True

    def test_subclass_detect_false_when_no_markers(self, tmp_path):
        from pactkit.skills.visualize import TopologyParser, WorkflowGraph
        class TestParser(TopologyParser):
            markers = ['nonexistent.yml']
            def parse(self, root):
                return WorkflowGraph()
        p = TestParser()
        assert p.detect(tmp_path) is False

    def test_subclass_detect_finds_directory_marker(self, tmp_path):
        from pactkit.skills.visualize import TopologyParser, WorkflowGraph
        class TestParser(TopologyParser):
            markers = ['config/']
            def parse(self, root):
                return WorkflowGraph()
        (tmp_path / 'config').mkdir()
        p = TestParser()
        assert p.detect(tmp_path) is True

    def test_parse_is_abstract(self):
        from pactkit.skills.visualize import TopologyParser
        import pytest
        class Incomplete(TopologyParser):
            markers = ['x']
            # No parse() defined
        with pytest.raises(TypeError):
            Incomplete()


# ── _TOPOLOGY_MARKERS tests (R2) ─────────────────────────────────────

class TestTopologyMarkers:
    """Test _TOPOLOGY_MARKERS constant."""

    def test_has_pdca_markers(self):
        from pactkit.skills.visualize import _TOPOLOGY_MARKERS
        assert 'pdca' in _TOPOLOGY_MARKERS
        assert '.claude/commands/' in _TOPOLOGY_MARKERS['pdca']

    def test_has_service_markers(self):
        from pactkit.skills.visualize import _TOPOLOGY_MARKERS
        assert 'service' in _TOPOLOGY_MARKERS
        assert 'docker-compose.yml' in _TOPOLOGY_MARKERS['service']

    def test_has_frontend_markers(self):
        from pactkit.skills.visualize import _TOPOLOGY_MARKERS
        assert 'frontend' in _TOPOLOGY_MARKERS
        assert 'next.config.js' in _TOPOLOGY_MARKERS['frontend']


# ── detect_topology() tests (R3) ─────────────────────────────────────

class TestDetectTopology:
    """Test detect_topology() dispatcher."""

    def test_detects_pdca(self, tmp_path):
        from pactkit.skills.visualize import detect_topology
        (tmp_path / '.claude' / 'commands').mkdir(parents=True)
        result = detect_topology(tmp_path)
        assert 'pdca' in result

    def test_detects_service(self, tmp_path):
        from pactkit.skills.visualize import detect_topology
        (tmp_path / 'docker-compose.yml').write_text('version: "3"', encoding='utf-8')
        result = detect_topology(tmp_path)
        assert 'service' in result

    def test_detects_frontend(self, tmp_path):
        from pactkit.skills.visualize import detect_topology
        (tmp_path / 'next.config.js').write_text('module.exports = {}', encoding='utf-8')
        result = detect_topology(tmp_path)
        assert 'frontend' in result

    def test_returns_empty_for_unknown(self, tmp_path):
        from pactkit.skills.visualize import detect_topology
        result = detect_topology(tmp_path)
        assert result == []

    def test_multi_topology(self, tmp_path):
        from pactkit.skills.visualize import detect_topology
        (tmp_path / 'docker-compose.yml').write_text('version: "3"', encoding='utf-8')
        (tmp_path / 'next.config.js').write_text('module.exports = {}', encoding='utf-8')
        result = detect_topology(tmp_path)
        assert 'service' in result
        assert 'frontend' in result


# ── _TOPOLOGY_PARSERS registry tests (R4) ────────────────────────────

class TestTopologyParsersRegistry:
    """Test _TOPOLOGY_PARSERS registry exists."""

    def test_registry_is_dict(self):
        from pactkit.skills.visualize import _TOPOLOGY_PARSERS
        assert isinstance(_TOPOLOGY_PARSERS, dict)
