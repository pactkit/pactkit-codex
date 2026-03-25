"""STORY-slim-032: TreeSitterAnalyzer base class + Go adapter.

Tests verify:
1. TreeSitterAnalyzer creation with Go language/queries
2. GoAnalyzer.extract_imports() with single/block/named imports
3. GoAnalyzer.extract_functions_and_calls() with top-level funcs, methods with receivers
4. GoAnalyzer handles FileNotFoundError, UnicodeDecodeError gracefully
5. _select_analyzer("go") returns GoAnalyzer
6. _select_analyzer("python") returns PythonAnalyzer
7. _select_analyzer with ImportError fallback
8. Python output unchanged (AC7)
"""
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


# Go source samples used across tests
GO_SINGLE_IMPORT = b'''package main

import "fmt"

func main() {
    fmt.Println("Hello")
}
'''

GO_BLOCK_IMPORT = b'''package main

import (
    "fmt"
    "net/http"
    "os"
)

func main() {
    fmt.Println("Hello")
}
'''

GO_NAMED_IMPORT = b'''package main

import (
    alias "path/filepath"
    "os"
)

func main() {
    alias.Join("a", "b")
    os.Exit(0)
}
'''

GO_FUNCTIONS = b'''package main

import "fmt"

func main() {
    fmt.Println("Hello")
    helper()
}

func helper() {
    fmt.Println("Helping")
}
'''

GO_METHOD_RECEIVER = b'''package server

import "fmt"

type Server struct {
    name string
}

func (s *Server) HandleRequest() {
    s.validateInput()
    fmt.Println("handled")
}

func (s *Server) validateInput() {
    fmt.Println("validating")
}

func NewServer() *Server {
    return &Server{}
}
'''


# ==============================================================================
# Test 1: TreeSitterAnalyzer — creation
# ==============================================================================
class TestTreeSitterAnalyzerCreation:
    def test_tree_sitter_available(self):
        """tree-sitter must be importable in this environment."""
        from tree_sitter import Language, Parser, Query, QueryCursor  # noqa: F401
        import tree_sitter_go  # noqa: F401

    def test_go_analyzer_instantiates(self):
        """GoAnalyzer() instantiates without error."""
        g = _exec_visualize()
        GoAnalyzer = g.get('GoAnalyzer')
        if GoAnalyzer is None:
            import pytest
            pytest.skip("GoAnalyzer not yet implemented")
        analyzer = GoAnalyzer()
        assert analyzer is not None

    def test_go_analyzer_is_language_analyzer(self):
        """GoAnalyzer is a subclass of LanguageAnalyzer."""
        g = _exec_visualize()
        LanguageAnalyzer = g['LanguageAnalyzer']
        GoAnalyzer = g.get('GoAnalyzer')
        if GoAnalyzer is None:
            import pytest
            pytest.skip("GoAnalyzer not yet implemented")
        assert issubclass(GoAnalyzer, LanguageAnalyzer)

    def test_tree_sitter_analyzer_is_language_analyzer(self):
        """TreeSitterAnalyzer is a subclass of LanguageAnalyzer."""
        g = _exec_visualize()
        LanguageAnalyzer = g['LanguageAnalyzer']
        TreeSitterAnalyzer = g.get('TreeSitterAnalyzer')
        if TreeSitterAnalyzer is None:
            import pytest
            pytest.skip("TreeSitterAnalyzer not yet implemented")
        assert issubclass(TreeSitterAnalyzer, LanguageAnalyzer)


# ==============================================================================
# Test 2: GoAnalyzer.extract_imports()
# ==============================================================================
class TestGoAnalyzerExtractImports:
    def _get_go_analyzer(self):
        g = _exec_visualize()
        GoAnalyzer = g.get('GoAnalyzer')
        if GoAnalyzer is None:
            import pytest
            pytest.skip("GoAnalyzer not yet implemented")
        return GoAnalyzer()

    def test_single_import(self, tmp_path):
        """import \"fmt\" → ['fmt']"""
        analyzer = self._get_go_analyzer()
        f = tmp_path / 'main.go'
        f.write_bytes(GO_SINGLE_IMPORT)
        result = analyzer.extract_imports(f)
        assert 'fmt' in result

    def test_block_imports(self, tmp_path):
        """Block import with fmt, net/http, os → all three returned."""
        analyzer = self._get_go_analyzer()
        f = tmp_path / 'main.go'
        f.write_bytes(GO_BLOCK_IMPORT)
        result = analyzer.extract_imports(f)
        assert 'fmt' in result
        assert 'net/http' in result
        assert 'os' in result

    def test_named_import_returns_path_not_alias(self, tmp_path):
        """Named import: alias \"path/filepath\" → 'path/filepath', not 'alias'."""
        analyzer = self._get_go_analyzer()
        f = tmp_path / 'main.go'
        f.write_bytes(GO_NAMED_IMPORT)
        result = analyzer.extract_imports(f)
        assert 'path/filepath' in result
        assert 'alias' not in result

    def test_returns_list(self, tmp_path):
        """extract_imports returns a list."""
        analyzer = self._get_go_analyzer()
        f = tmp_path / 'main.go'
        f.write_bytes(GO_SINGLE_IMPORT)
        result = analyzer.extract_imports(f)
        assert isinstance(result, list)

    def test_empty_for_no_imports(self, tmp_path):
        """Go file with no imports returns []."""
        analyzer = self._get_go_analyzer()
        f = tmp_path / 'main.go'
        f.write_bytes(b'package main\n\nfunc main() {}\n')
        result = analyzer.extract_imports(f)
        assert isinstance(result, list)
        assert 'fmt' not in result


# ==============================================================================
# Test 3: GoAnalyzer.extract_functions_and_calls()
# ==============================================================================
class TestGoAnalyzerExtractFunctionsAndCalls:
    def _get_go_analyzer(self):
        g = _exec_visualize()
        GoAnalyzer = g.get('GoAnalyzer')
        if GoAnalyzer is None:
            import pytest
            pytest.skip("GoAnalyzer not yet implemented")
        return GoAnalyzer()

    def test_returns_tuple(self, tmp_path):
        """extract_functions_and_calls returns a 2-tuple."""
        analyzer = self._get_go_analyzer()
        f = tmp_path / 'main.go'
        f.write_bytes(GO_FUNCTIONS)
        result = analyzer.extract_functions_and_calls(f)
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_top_level_function_registered(self, tmp_path):
        """Top-level func main() and func helper() are in func_registry."""
        analyzer = self._get_go_analyzer()
        f = tmp_path / 'main.go'
        f.write_bytes(GO_FUNCTIONS)
        func_registry, call_edges = analyzer.extract_functions_and_calls(f)
        assert 'main' in func_registry
        assert 'helper' in func_registry

    def test_method_receiver_registered_as_class_dot_method(self, tmp_path):
        """func (s *Server) HandleRequest() → 'Server.HandleRequest' in func_registry."""
        analyzer = self._get_go_analyzer()
        f = tmp_path / 'server.go'
        f.write_bytes(GO_METHOD_RECEIVER)
        func_registry, call_edges = analyzer.extract_functions_and_calls(f)
        assert 'Server.HandleRequest' in func_registry, f"func_registry keys: {list(func_registry.keys())}"

    def test_plain_function_call_extracted(self, tmp_path):
        """main() calls helper() → 'helper' in call_edges['main']."""
        analyzer = self._get_go_analyzer()
        f = tmp_path / 'main.go'
        f.write_bytes(GO_FUNCTIONS)
        func_registry, call_edges = analyzer.extract_functions_and_calls(f)
        # 'main' should call 'helper'
        main_callees = call_edges.get('main', [])
        assert 'helper' in main_callees, f"call_edges for main: {main_callees}"

    def test_method_receiver_calls_extracted(self, tmp_path):
        """HandleRequest() calls validateInput() → validateInput in callees."""
        analyzer = self._get_go_analyzer()
        f = tmp_path / 'server.go'
        f.write_bytes(GO_METHOD_RECEIVER)
        func_registry, call_edges = analyzer.extract_functions_and_calls(f)
        # Server.HandleRequest should have validateInput in callees
        handle_key = 'Server.HandleRequest'
        handle_callees = call_edges.get(handle_key, [])
        # validateInput could appear as 'validateInput' or 'Server.validateInput'
        callee_names = ' '.join(handle_callees)
        assert 'validateInput' in callee_names, (
            f"Expected 'validateInput' in callees of {handle_key}: {handle_callees}"
        )

    def test_func_registry_stem_is_file_stem(self, tmp_path):
        """func_registry values are the file stem."""
        analyzer = self._get_go_analyzer()
        f = tmp_path / 'myservice.go'
        f.write_bytes(GO_FUNCTIONS)
        func_registry, call_edges = analyzer.extract_functions_and_calls(f)
        assert func_registry.get('main') == 'myservice'


# ==============================================================================
# Test 4: GoAnalyzer error handling
# ==============================================================================
class TestGoAnalyzerErrorHandling:
    def _get_go_analyzer(self):
        g = _exec_visualize()
        GoAnalyzer = g.get('GoAnalyzer')
        if GoAnalyzer is None:
            import pytest
            pytest.skip("GoAnalyzer not yet implemented")
        return GoAnalyzer()

    def test_extract_imports_file_not_found(self, tmp_path):
        """Missing file → extract_imports returns []."""
        analyzer = self._get_go_analyzer()
        f = tmp_path / 'nonexistent.go'
        result = analyzer.extract_imports(f)
        assert result == []

    def test_extract_functions_file_not_found(self, tmp_path):
        """Missing file → extract_functions_and_calls returns ({}, {})."""
        analyzer = self._get_go_analyzer()
        f = tmp_path / 'nonexistent.go'
        func_registry, call_edges = analyzer.extract_functions_and_calls(f)
        assert func_registry == {}
        assert call_edges == {}


# ==============================================================================
# Test 5: _select_analyzer("go") returns GoAnalyzer
# ==============================================================================
class TestSelectAnalyzerGo:
    def test_select_go_returns_go_analyzer(self):
        """_select_analyzer('go') returns a GoAnalyzer instance."""
        g = _exec_visualize()
        _select_analyzer = g.get('_select_analyzer')
        if _select_analyzer is None:
            import pytest
            pytest.skip("_select_analyzer not yet implemented")
        GoAnalyzer = g.get('GoAnalyzer')
        if GoAnalyzer is None:
            import pytest
            pytest.skip("GoAnalyzer not yet implemented")
        analyzer = _select_analyzer('go')
        assert isinstance(analyzer, GoAnalyzer)

    def test_select_go_has_tree_sitter_flag(self):
        """_HAS_TREE_SITTER must be True when tree-sitter is installed."""
        g = _exec_visualize()
        _HAS_TREE_SITTER = g.get('_HAS_TREE_SITTER')
        if _HAS_TREE_SITTER is None:
            import pytest
            pytest.skip("_HAS_TREE_SITTER not yet defined")
        assert _HAS_TREE_SITTER is True


# ==============================================================================
# Test 6: _select_analyzer("python") returns PythonAnalyzer
# ==============================================================================
class TestSelectAnalyzerPython:
    def test_select_python_returns_python_analyzer(self):
        """_select_analyzer('python') returns a PythonAnalyzer instance."""
        g = _exec_visualize()
        _select_analyzer = g.get('_select_analyzer')
        if _select_analyzer is None:
            import pytest
            pytest.skip("_select_analyzer not yet implemented")
        PythonAnalyzer = g['PythonAnalyzer']
        analyzer = _select_analyzer('python')
        assert isinstance(analyzer, PythonAnalyzer)

    def test_select_python_always_returns_python_analyzer(self):
        """_select_analyzer('python') returns PythonAnalyzer regardless of tree-sitter."""
        g = _exec_visualize()
        _select_analyzer = g.get('_select_analyzer')
        if _select_analyzer is None:
            import pytest
            pytest.skip("_select_analyzer not yet implemented")
        PythonAnalyzer = g['PythonAnalyzer']
        analyzer = _select_analyzer('python')
        assert type(analyzer).__name__ == 'PythonAnalyzer'


# ==============================================================================
# Test 7: _select_analyzer fallback behavior
# ==============================================================================
class TestSelectAnalyzerFallback:
    def test_unknown_stack_falls_back_to_python(self):
        """_select_analyzer('ruby') falls back to PythonAnalyzer."""
        g = _exec_visualize()
        _select_analyzer = g.get('_select_analyzer')
        if _select_analyzer is None:
            import pytest
            pytest.skip("_select_analyzer not yet implemented")
        PythonAnalyzer = g['PythonAnalyzer']
        analyzer = _select_analyzer('ruby')
        assert isinstance(analyzer, PythonAnalyzer)

    def test_select_analyzer_returns_language_analyzer(self):
        """_select_analyzer always returns a LanguageAnalyzer instance."""
        g = _exec_visualize()
        _select_analyzer = g.get('_select_analyzer')
        if _select_analyzer is None:
            import pytest
            pytest.skip("_select_analyzer not yet implemented")
        LanguageAnalyzer = g['LanguageAnalyzer']
        for stack in ['python', 'go', 'java', 'node', 'unknown']:
            analyzer = _select_analyzer(stack)
            assert isinstance(analyzer, LanguageAnalyzer), (
                f"_select_analyzer('{stack}') returned {type(analyzer)}, not LanguageAnalyzer"
            )


# ==============================================================================
# Test 8: Python output unchanged (AC7)
# ==============================================================================
class TestPythonOutputUnchanged:
    def test_python_project_uses_python_analyzer(self, tmp_path):
        """For a Python project, visualize() uses PythonAnalyzer (unchanged behavior)."""
        g = _exec_visualize()
        _select_analyzer = g.get('_select_analyzer')
        _detect_stack = g.get('_detect_stack')
        if _select_analyzer is None or _detect_stack is None:
            import pytest
            pytest.skip("_select_analyzer/_detect_stack not yet implemented")
        PythonAnalyzer = g['PythonAnalyzer']

        # Python project: pyproject.toml marker
        (tmp_path / 'pyproject.toml').write_text('[project]\nname = "test"\n', encoding='utf-8')

        stack = _detect_stack(tmp_path)
        assert stack == 'python'

        analyzer = _select_analyzer(stack)
        assert isinstance(analyzer, PythonAnalyzer)

    def test_python_analyzer_still_extracts_py_functions(self, tmp_path):
        """PythonAnalyzer still works correctly after _select_analyzer is added."""
        g = _exec_visualize()
        _select_analyzer = g.get('_select_analyzer')
        if _select_analyzer is None:
            import pytest
            pytest.skip("_select_analyzer not yet implemented")

        f = tmp_path / 'sample.py'
        f.write_text(
            'def foo():\n'
            '    bar()\n'
            '\n'
            'def bar():\n'
            '    pass\n',
            encoding='utf-8'
        )

        analyzer = _select_analyzer('python')
        func_registry, call_edges = analyzer.extract_functions_and_calls(f)
        assert 'foo' in func_registry
        assert 'bar' in func_registry
        assert 'bar' in call_edges.get('foo', [])

    def test_visualize_and_impact_use_select_analyzer(self, tmp_path):
        """visualize() and impact() call _select_analyzer (not hardcoded PythonAnalyzer)."""
        g = _exec_visualize()
        # Verify the source code uses _select_analyzer
        from pactkit.prompts import VISUALIZE_SOURCE
        # After implementation, 'PythonAnalyzer()  # TODO' should be gone
        # and '_select_analyzer(' should appear in visualize() and impact()
        # We check for presence of '_select_analyzer' in source
        assert '_select_analyzer' in VISUALIZE_SOURCE, (
            "_select_analyzer must appear in visualize.py source"
        )


# ==============================================================================
# Test 9: GoAnalyzer end-to-end via _build_call_graph (AC2 analog)
# ==============================================================================
class TestGoAnalyzerInCallGraph:
    def test_go_file_graph_via_analyzer(self, tmp_path):
        """GoAnalyzer.extract_imports returns a list that can be processed."""
        g = _exec_visualize()
        GoAnalyzer = g.get('GoAnalyzer')
        if GoAnalyzer is None:
            import pytest
            pytest.skip("GoAnalyzer not yet implemented")

        f = tmp_path / 'main.go'
        f.write_bytes(GO_BLOCK_IMPORT)
        analyzer = GoAnalyzer()
        imports = analyzer.extract_imports(f)
        assert len(imports) >= 3  # fmt, net/http, os

    def test_go_call_graph_extracts_edges(self, tmp_path):
        """GoAnalyzer can drive _build_call_graph with actual Go files."""
        g = _exec_visualize()
        GoAnalyzer = g.get('GoAnalyzer')
        _build_call_graph = g.get('_build_call_graph')
        if GoAnalyzer is None or _build_call_graph is None:
            import pytest
            pytest.skip("GoAnalyzer or _build_call_graph not yet available")

        f = tmp_path / 'main.go'
        f.write_bytes(GO_FUNCTIONS)
        # Scan files manually (Go .go files)
        all_go_files = [f]
        analyzer = GoAnalyzer()
        dest, content = _build_call_graph(
            tmp_path, all_go_files, focus=None, entry=None, analyzer=analyzer
        )
        assert 'graph TD' in content
        # Both main and helper should appear in the call graph
        assert 'main' in content
        assert 'helper' in content
