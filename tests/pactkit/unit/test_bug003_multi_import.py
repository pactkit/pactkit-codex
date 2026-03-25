"""BUG-003: visualize.py ast.Import only captures last alias in multi-import.

When a file has `import a, b, c`, the file-level dependency graph should
create edges for ALL imported modules, not just the last one.
"""
import textwrap

from pactkit.skills.visualize import _build_file_graph, _scan_files


class TestMultiNameImportEdges:
    """_build_file_graph must emit edges for every alias in `import a, b, c`."""

    def _setup_project(self, tmp_path):
        """Create a minimal project with multi-import consumer."""
        src = tmp_path / "src"
        src.mkdir()
        (src / "alpha.py").write_text("X = 1\n", encoding="utf-8")
        (src / "beta.py").write_text("Y = 2\n", encoding="utf-8")
        (src / "gamma.py").write_text("Z = 3\n", encoding="utf-8")
        (src / "consumer.py").write_text(
            textwrap.dedent("""\
                import alpha, beta, gamma
                print(alpha.X, beta.Y, gamma.Z)
            """),
            encoding="utf-8",
        )
        return src

    def test_all_aliases_produce_edges(self, tmp_path):
        """Edge exists for every module in `import alpha, beta, gamma`."""
        src = self._setup_project(tmp_path)
        all_files, module_index, file_to_node = _scan_files(src)
        dest, content = _build_file_graph(src, all_files, module_index, file_to_node, focus=None)

        # consumer should have edges to all three
        consumer_id = file_to_node[src / "consumer.py"]
        alpha_id = file_to_node[src / "alpha.py"]
        beta_id = file_to_node[src / "beta.py"]
        gamma_id = file_to_node[src / "gamma.py"]

        assert f"{consumer_id} --> {alpha_id}" in content, "Missing edge for alpha"
        assert f"{consumer_id} --> {beta_id}" in content, "Missing edge for beta"
        assert f"{consumer_id} --> {gamma_id}" in content, "Missing edge for gamma"

    def test_single_import_still_works(self, tmp_path):
        """Regression: single `import X` still produces one edge."""
        src = tmp_path / "src"
        src.mkdir()
        (src / "util.py").write_text("pass\n", encoding="utf-8")
        (src / "main.py").write_text("import util\n", encoding="utf-8")

        all_files, module_index, file_to_node = _scan_files(src)
        dest, content = _build_file_graph(src, all_files, module_index, file_to_node, focus=None)

        main_id = file_to_node[src / "main.py"]
        util_id = file_to_node[src / "util.py"]
        assert f"{main_id} --> {util_id}" in content

    def test_no_duplicate_edges(self, tmp_path):
        """Same (consumer, provider) pair should not appear twice."""
        src = tmp_path / "src"
        src.mkdir()
        (src / "lib.py").write_text("pass\n", encoding="utf-8")
        (src / "app.py").write_text(
            textwrap.dedent("""\
                import lib
                import lib
            """),
            encoding="utf-8",
        )

        all_files, module_index, file_to_node = _scan_files(src)
        dest, content = _build_file_graph(src, all_files, module_index, file_to_node, focus=None)

        app_id = file_to_node[src / "app.py"]
        lib_id = file_to_node[src / "lib.py"]
        edge = f"{app_id} --> {lib_id}"
        # Count occurrences of this edge in the graph
        assert content.count(edge) == 1, f"Duplicate edge found: {edge}"
