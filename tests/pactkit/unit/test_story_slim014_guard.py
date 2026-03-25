"""Tests for pactkit guard (STORY-slim-014 R1)."""
from pactkit.guards import check_init_markers


class TestCheckInitMarkers:
    """Scenario 1 from spec: pactkit guard replaces Init Guard prompt."""

    def test_all_markers_present(self, tmp_path):
        """Given all markers exist, guard returns (True, [])."""
        # Create markers
        (tmp_path / ".claude").mkdir()
        yaml_path = tmp_path / ".claude" / "pactkit.yaml"
        yaml_path.write_text('version: "2.2.0"\ndeveloper: "slim"\n')
        (tmp_path / "docs" / "product").mkdir(parents=True)
        (tmp_path / "docs" / "product" / "sprint_board.md").write_text("# Sprint Board\n")
        (tmp_path / "docs" / "architecture" / "graphs").mkdir(parents=True)

        ok, missing = check_init_markers(tmp_path)
        assert ok is True
        assert missing == []

    def test_missing_sprint_board(self, tmp_path):
        """Given sprint_board.md missing, guard returns (False, [...])."""
        (tmp_path / ".claude").mkdir()
        (tmp_path / ".claude" / "pactkit.yaml").write_text('developer: "slim"\n')
        (tmp_path / "docs" / "architecture" / "graphs").mkdir(parents=True)

        ok, missing = check_init_markers(tmp_path)
        assert ok is False
        assert any("sprint_board" in m for m in missing)

    def test_missing_pactkit_yaml(self, tmp_path):
        """Given pactkit.yaml missing, guard returns (False, [...])."""
        (tmp_path / "docs" / "product").mkdir(parents=True)
        (tmp_path / "docs" / "product" / "sprint_board.md").write_text("# Sprint Board\n")
        (tmp_path / "docs" / "architecture" / "graphs").mkdir(parents=True)

        ok, missing = check_init_markers(tmp_path)
        assert ok is False
        assert any("pactkit.yaml" in m for m in missing)

    def test_missing_graphs_dir(self, tmp_path):
        """Given graphs/ dir missing, guard returns (False, [...])."""
        (tmp_path / ".claude").mkdir()
        (tmp_path / ".claude" / "pactkit.yaml").write_text('developer: "slim"\n')
        (tmp_path / "docs" / "product").mkdir(parents=True)
        (tmp_path / "docs" / "product" / "sprint_board.md").write_text("# Sprint Board\n")

        ok, missing = check_init_markers(tmp_path)
        assert ok is False
        assert any("graphs" in m for m in missing)

    def test_empty_developer_warns(self, tmp_path):
        """Given developer is empty, guard returns (True, []) with warning in messages."""
        (tmp_path / ".claude").mkdir()
        (tmp_path / ".claude" / "pactkit.yaml").write_text('developer: ""\n')
        (tmp_path / "docs" / "product").mkdir(parents=True)
        (tmp_path / "docs" / "product" / "sprint_board.md").write_text("# Sprint Board\n")
        (tmp_path / "docs" / "architecture" / "graphs").mkdir(parents=True)

        ok, _missing = check_init_markers(tmp_path)
        # All markers present, but developer empty is a warning, not a failure
        assert ok is True

    def test_all_missing(self, tmp_path):
        """Given nothing exists, guard returns (False, [3 items])."""
        ok, missing = check_init_markers(tmp_path)
        assert ok is False
        assert len(missing) == 3
