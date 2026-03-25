"""STORY-020: Visualize Horizon Limit (--depth and --max-nodes)."""
from pactkit.prompts.commands import COMMANDS_CONTENT
from pactkit.skills.visualize import visualize


class TestDepthParameter:
    """visualize must accept --depth and limit graph traversal."""

    def test_depth_arg_accepted(self, tmp_path):
        """R1: --depth parameter should not raise an error."""
        # Create a minimal Python project
        (tmp_path / "a.py").write_text("import b\n")
        (tmp_path / "b.py").write_text("import c\n")
        (tmp_path / "c.py").write_text("import d\n")
        (tmp_path / "d.py").write_text("x = 1\n")
        (tmp_path / "docs/architecture/graphs").mkdir(parents=True)
        result = visualize(str(tmp_path), depth=2)
        assert "Graph" in result or "graph" in result.lower()

    def test_depth_limits_file_graph(self, tmp_path):
        """S1: --depth 2 should limit to 2 hops from root modules."""
        (tmp_path / "a.py").write_text("import b\n")
        (tmp_path / "b.py").write_text("import c\n")
        (tmp_path / "c.py").write_text("import d\n")
        (tmp_path / "d.py").write_text("x = 1\n")
        (tmp_path / "docs/architecture/graphs").mkdir(parents=True)
        result = visualize(str(tmp_path), depth=1)
        graph_path = tmp_path / "docs/architecture/graphs/code_graph.mmd"
        content = graph_path.read_text()
        # With depth=1, we should see a, b (1 hop) but not c, d
        # The exact filtering depends on which nodes are "roots"
        # At minimum, deeper nodes should be excluded
        lines = content.strip().split("\n")
        node_ids = [l.strip().split("[")[0].strip() for l in lines if "[" in l and "click" not in l]
        # Should have fewer nodes than a full scan (which has 4)
        assert len(node_ids) < 4, f"Depth=1 should limit nodes, got {len(node_ids)}: {node_ids}"

    def test_default_no_depth_unchanged(self, tmp_path):
        """S3: Default behavior (no depth) must include all nodes."""
        (tmp_path / "a.py").write_text("import b\n")
        (tmp_path / "b.py").write_text("import c\n")
        (tmp_path / "c.py").write_text("x = 1\n")
        (tmp_path / "docs/architecture/graphs").mkdir(parents=True)
        result = visualize(str(tmp_path))
        graph_path = tmp_path / "docs/architecture/graphs/code_graph.mmd"
        content = graph_path.read_text()
        # All 3 files should be present
        assert "a_py" in content
        assert "b_py" in content
        assert "c_py" in content


class TestMaxNodes:
    """visualize must accept --max-nodes and truncate."""

    def test_max_nodes_truncates(self, tmp_path):
        """S2: --max-nodes should truncate and add a NOTE."""
        # Create many files
        for i in range(10):
            (tmp_path / f"mod{i}.py").write_text(f"x = {i}\n")
        (tmp_path / "docs/architecture/graphs").mkdir(parents=True)
        result = visualize(str(tmp_path), max_nodes=5)
        graph_path = tmp_path / "docs/architecture/graphs/code_graph.mmd"
        content = graph_path.read_text()
        assert "more nodes" in content.lower() or "NOTE" in content

    def test_max_nodes_default_no_truncation(self, tmp_path):
        """Default max_nodes (0=unlimited) should not truncate small graphs."""
        (tmp_path / "a.py").write_text("x = 1\n")
        (tmp_path / "b.py").write_text("x = 2\n")
        (tmp_path / "docs/architecture/graphs").mkdir(parents=True)
        result = visualize(str(tmp_path))
        graph_path = tmp_path / "docs/architecture/graphs/code_graph.mmd"
        content = graph_path.read_text()
        assert "NOTE" not in content


class TestPromptGuidance:
    """Plan and Act prompts should recommend --focus --depth for large projects."""

    def test_plan_prompt_mentions_depth(self):
        """S4: Plan prompt should mention --depth for large codebases."""
        prompt = COMMANDS_CONTENT["project-plan.md"]
        assert "--depth" in prompt

    def test_plan_prompt_mentions_focus_heuristic(self):
        """S4: Plan prompt should have a heuristic for large codebases."""
        prompt = COMMANDS_CONTENT["project-plan.md"]
        assert "--focus" in prompt  # STORY-slim-020: replaced "50+ files" with targeted --focus

    def test_act_prompt_mentions_depth(self):
        """Act prompt should also mention --depth."""
        prompt = COMMANDS_CONTENT["project-act.md"]
        assert "--depth" in prompt
