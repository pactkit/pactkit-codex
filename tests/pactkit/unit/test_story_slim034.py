"""Tests for STORY-slim-034: TS/JS LanguageAnalyzer adapter."""
import importlib.util
import pathlib
import textwrap

# Load visualize.py as standalone module
_vis_path = pathlib.Path(__file__).resolve().parents[2] / "src" / "pactkit" / "skills" / "visualize.py"
_spec = importlib.util.spec_from_file_location("visualize", _vis_path)
vis = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(vis)


# ---------------------------------------------------------------------------
# TSAnalyzer Creation
# ---------------------------------------------------------------------------
class TestTSAnalyzerCreation:
    def test_tree_sitter_typescript_available(self):
        import tree_sitter_typescript  # noqa: F401

    def test_ts_analyzer_instantiates(self):
        analyzer = vis.TSAnalyzer()
        assert analyzer is not None

    def test_ts_analyzer_is_language_analyzer(self):
        analyzer = vis.TSAnalyzer()
        assert isinstance(analyzer, vis.LanguageAnalyzer)

    def test_ts_analyzer_is_tree_sitter_analyzer(self):
        analyzer = vis.TSAnalyzer()
        assert isinstance(analyzer, vis.TreeSitterAnalyzer)


# ---------------------------------------------------------------------------
# Import Extraction
# ---------------------------------------------------------------------------
class TestTSAnalyzerExtractImports:
    def test_es_module_import(self, tmp_path):
        f = tmp_path / "app.ts"
        f.write_text('import { Config } from "./config";\n')
        result = vis.TSAnalyzer().extract_imports(f)
        assert any("./config" in r for r in result)

    def test_default_import(self, tmp_path):
        f = tmp_path / "app.ts"
        f.write_text('import express from "express";\n')
        result = vis.TSAnalyzer().extract_imports(f)
        assert any("express" in r for r in result)

    def test_commonjs_require(self, tmp_path):
        f = tmp_path / "app.js"
        f.write_text('const path = require("path");\n')
        result = vis.TSAnalyzer().extract_imports(f)
        assert any("path" in r for r in result)

    def test_reexport(self, tmp_path):
        f = tmp_path / "index.ts"
        f.write_text('export { handler } from "./handler";\n')
        result = vis.TSAnalyzer().extract_imports(f)
        assert any("./handler" in r for r in result)

    def test_multiple_imports(self, tmp_path):
        f = tmp_path / "app.ts"
        f.write_text('import { A } from "./a";\nimport { B } from "./b";\n')
        result = vis.TSAnalyzer().extract_imports(f)
        assert len(result) >= 2

    def test_returns_list(self, tmp_path):
        f = tmp_path / "empty.ts"
        f.write_text("const x = 1;\n")
        result = vis.TSAnalyzer().extract_imports(f)
        assert isinstance(result, list)

    def test_empty_for_no_imports(self, tmp_path):
        f = tmp_path / "empty.ts"
        f.write_text("const x = 1;\n")
        assert vis.TSAnalyzer().extract_imports(f) == []


# ---------------------------------------------------------------------------
# Function and Call Extraction
# ---------------------------------------------------------------------------
class TestTSAnalyzerExtractFunctionsAndCalls:
    def test_returns_tuple(self, tmp_path):
        f = tmp_path / "app.ts"
        f.write_text("function foo() {}\n")
        result = vis.TSAnalyzer().extract_functions_and_calls(f)
        assert isinstance(result, tuple) and len(result) == 2

    def test_named_function(self, tmp_path):
        f = tmp_path / "app.ts"
        f.write_text("function handleRequest(req: Request) { validate(req); }\n")
        func_registry, call_edges = vis.TSAnalyzer().extract_functions_and_calls(f)
        assert "handleRequest" in func_registry
        assert any("validate" in c for c in call_edges.get("handleRequest", []))

    def test_arrow_function(self, tmp_path):
        f = tmp_path / "app.ts"
        f.write_text('export const handler = async (req: Request) => { validateInput(req); };\n')
        func_registry, call_edges = vis.TSAnalyzer().extract_functions_and_calls(f)
        assert "handler" in func_registry
        assert any("validateInput" in c for c in call_edges.get("handler", []))

    def test_class_method(self, tmp_path):
        f = tmp_path / "server.ts"
        f.write_text(textwrap.dedent("""\
            class Server {
                listen(port: number) {
                    this.setup();
                }
            }
        """))
        func_registry, call_edges = vis.TSAnalyzer().extract_functions_and_calls(f)
        assert "Server.listen" in func_registry

    def test_method_call_extracted(self, tmp_path):
        f = tmp_path / "app.ts"
        f.write_text('function run() { console.log("hi"); }\n')
        _, call_edges = vis.TSAnalyzer().extract_functions_and_calls(f)
        calls = call_edges.get("run", [])
        assert any("console.log" in c for c in calls)

    def test_func_registry_stem(self, tmp_path):
        f = tmp_path / "myModule.ts"
        f.write_text("function foo() {}\n")
        func_registry, _ = vis.TSAnalyzer().extract_functions_and_calls(f)
        assert func_registry.get("foo") == "myModule"


# ---------------------------------------------------------------------------
# Error Handling
# ---------------------------------------------------------------------------
class TestTSAnalyzerErrorHandling:
    def test_extract_imports_file_not_found(self):
        result = vis.TSAnalyzer().extract_imports(pathlib.Path("/nonexistent/file.ts"))
        assert result == []

    def test_extract_functions_file_not_found(self):
        result = vis.TSAnalyzer().extract_functions_and_calls(pathlib.Path("/nonexistent/file.ts"))
        assert result == ({}, {})

    def test_extract_imports_empty_file(self, tmp_path):
        f = tmp_path / "empty.ts"
        f.write_text("")
        assert vis.TSAnalyzer().extract_imports(f) == []

    def test_extract_functions_empty_file(self, tmp_path):
        f = tmp_path / "empty.ts"
        f.write_text("")
        assert vis.TSAnalyzer().extract_functions_and_calls(f) == ({}, {})


# ---------------------------------------------------------------------------
# _select_analyzer
# ---------------------------------------------------------------------------
class TestSelectAnalyzerNode:
    def test_select_node_returns_ts_analyzer(self):
        analyzer = vis._select_analyzer("node")
        assert isinstance(analyzer, vis.TSAnalyzer)

    def test_select_node_is_language_analyzer(self):
        analyzer = vis._select_analyzer("node")
        assert isinstance(analyzer, vis.LanguageAnalyzer)


class TestSelectAnalyzerFallbackForTS:
    def test_all_stacks_return_language_analyzer(self):
        for stack in ("python", "go", "java", "node", "unknown"):
            analyzer = vis._select_analyzer(stack)
            assert isinstance(analyzer, vis.LanguageAnalyzer), f"Failed for {stack}"


# ---------------------------------------------------------------------------
# Multi-Extension Scanning (R5)
# ---------------------------------------------------------------------------
class TestMultiExtensionScanning:
    def _make_node_project(self, tmp_path):
        """Create a minimal Node project with both .ts and .js files."""
        (tmp_path / "package.json").write_text('{"name": "test"}')
        (tmp_path / "app.ts").write_text('import { helper } from "./helper";\nfunction main() { helper(); }\n')
        (tmp_path / "helper.js").write_text('function helper() { return 1; }\nmodule.exports = { helper };\n')
        return tmp_path

    def test_detect_stack_node(self, tmp_path):
        self._make_node_project(tmp_path)
        assert vis._detect_stack(tmp_path) == "node"

    def test_ts_and_js_files_both_scanned(self, tmp_path):
        self._make_node_project(tmp_path)
        files_ts, _, _ = vis._scan_files(tmp_path, file_ext=".ts")
        files_js, _, _ = vis._scan_files(tmp_path, file_ext=".js")
        ts_names = [f.name for f in files_ts]
        js_names = [f.name for f in files_js]
        assert "app.ts" in ts_names
        assert "helper.js" in js_names


# ---------------------------------------------------------------------------
# Detect Stack
# ---------------------------------------------------------------------------
class TestDetectStackNode:
    def test_package_json_detected_as_node(self, tmp_path):
        (tmp_path / "package.json").write_text("{}")
        assert vis._detect_stack(tmp_path) == "node"
