"""STORY-slim-030: LanguageAnalyzer interface + Python adapter.

Tests verify:
1. LanguageAnalyzer is abstract — cannot instantiate directly
2. PythonAnalyzer.extract_imports() returns module name strings
3. PythonAnalyzer.extract_functions_and_calls() returns (func_registry, call_edges)
4. PythonAnalyzer handles SyntaxError gracefully
5. _build_call_graph accepts analyzer param
6. _build_file_graph accepts analyzer param
7. _scan_call_edges accepts analyzer param
8. Default analyzer is PythonAnalyzer (backward compat)
9. Extensibility: DummyAnalyzer plugs into _build_call_graph
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


# ==============================================================================
# Test 1: LanguageAnalyzer is abstract
# ==============================================================================
class TestLanguageAnalyzerIsAbstract:
    def test_cannot_instantiate_directly(self):
        """LanguageAnalyzer must be an ABC — instantiating it raises TypeError."""
        g = _exec_visualize()
        LanguageAnalyzer = g['LanguageAnalyzer']
        try:
            LanguageAnalyzer()
            assert False, "Should have raised TypeError"
        except TypeError:
            pass  # Expected

    def test_must_implement_extract_imports(self):
        """Subclass without extract_imports implementation raises TypeError."""
        g = _exec_visualize()
        LanguageAnalyzer = g['LanguageAnalyzer']

        class NoImports(LanguageAnalyzer):
            def extract_functions_and_calls(self, file_path):
                return {}, {}

        try:
            NoImports()
            assert False, "Should have raised TypeError"
        except TypeError:
            pass

    def test_must_implement_extract_functions_and_calls(self):
        """Subclass without extract_functions_and_calls raises TypeError."""
        g = _exec_visualize()
        LanguageAnalyzer = g['LanguageAnalyzer']

        class NoCalls(LanguageAnalyzer):
            def extract_imports(self, file_path):
                return []

        try:
            NoCalls()
            assert False, "Should have raised TypeError"
        except TypeError:
            pass


# ==============================================================================
# Test 2: PythonAnalyzer.extract_imports()
# ==============================================================================
class TestPythonAnalyzerExtractImports:
    def test_extract_simple_import(self, tmp_path):
        """import os → ['os']"""
        g = _exec_visualize()
        PythonAnalyzer = g['PythonAnalyzer']
        f = tmp_path / 'sample.py'
        f.write_text('import os\n', encoding='utf-8')
        analyzer = PythonAnalyzer()
        result = analyzer.extract_imports(f)
        assert 'os' in result

    def test_extract_from_import(self, tmp_path):
        """from pathlib import Path → ['pathlib']"""
        g = _exec_visualize()
        PythonAnalyzer = g['PythonAnalyzer']
        f = tmp_path / 'sample.py'
        f.write_text('from pathlib import Path\n', encoding='utf-8')
        analyzer = PythonAnalyzer()
        result = analyzer.extract_imports(f)
        assert 'pathlib' in result

    def test_extract_relative_import(self, tmp_path):
        """from src.models import User → ['src.models']"""
        g = _exec_visualize()
        PythonAnalyzer = g['PythonAnalyzer']
        f = tmp_path / 'sample.py'
        f.write_text('from src.models import User\n', encoding='utf-8')
        analyzer = PythonAnalyzer()
        result = analyzer.extract_imports(f)
        assert 'src.models' in result

    def test_extract_multiple_imports(self, tmp_path):
        """Multiple imports returns all of them."""
        g = _exec_visualize()
        PythonAnalyzer = g['PythonAnalyzer']
        f = tmp_path / 'sample.py'
        f.write_text(
            'import os\n'
            'from pathlib import Path\n'
            'from src.models import User\n',
            encoding='utf-8'
        )
        analyzer = PythonAnalyzer()
        result = analyzer.extract_imports(f)
        assert 'os' in result
        assert 'pathlib' in result
        assert 'src.models' in result

    def test_returns_list(self, tmp_path):
        """extract_imports returns a list."""
        g = _exec_visualize()
        PythonAnalyzer = g['PythonAnalyzer']
        f = tmp_path / 'sample.py'
        f.write_text('import os\n', encoding='utf-8')
        analyzer = PythonAnalyzer()
        result = analyzer.extract_imports(f)
        assert isinstance(result, list)


# ==============================================================================
# Test 3: PythonAnalyzer.extract_functions_and_calls()
# ==============================================================================
class TestPythonAnalyzerExtractFunctionsAndCalls:
    def test_returns_tuple(self, tmp_path):
        """extract_functions_and_calls returns a 2-tuple."""
        g = _exec_visualize()
        PythonAnalyzer = g['PythonAnalyzer']
        f = tmp_path / 'sample.py'
        f.write_text('def foo():\n    pass\n', encoding='utf-8')
        analyzer = PythonAnalyzer()
        result = analyzer.extract_functions_and_calls(f)
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_func_registry_contains_function(self, tmp_path):
        """func_registry maps function name to file stem."""
        g = _exec_visualize()
        PythonAnalyzer = g['PythonAnalyzer']
        f = tmp_path / 'mymodule.py'
        f.write_text('def foo():\n    pass\n', encoding='utf-8')
        analyzer = PythonAnalyzer()
        func_registry, call_edges = analyzer.extract_functions_and_calls(f)
        assert 'foo' in func_registry

    def test_call_edges_contains_caller(self, tmp_path):
        """call_edges maps caller to list of callees."""
        g = _exec_visualize()
        PythonAnalyzer = g['PythonAnalyzer']
        f = tmp_path / 'mymodule.py'
        f.write_text(
            'def foo():\n'
            '    bar()\n'
            '\n'
            'def bar():\n'
            '    pass\n',
            encoding='utf-8'
        )
        analyzer = PythonAnalyzer()
        func_registry, call_edges = analyzer.extract_functions_and_calls(f)
        assert 'foo' in call_edges
        assert 'bar' in call_edges.get('foo', [])

    def test_class_method_qualified_name(self, tmp_path):
        """Class methods use ClassName.method_name in func_registry."""
        g = _exec_visualize()
        PythonAnalyzer = g['PythonAnalyzer']
        f = tmp_path / 'mymodule.py'
        f.write_text(
            'class Dog:\n'
            '    def bark(self):\n'
            '        pass\n',
            encoding='utf-8'
        )
        analyzer = PythonAnalyzer()
        func_registry, call_edges = analyzer.extract_functions_and_calls(f)
        assert 'Dog.bark' in func_registry


# ==============================================================================
# Test 4: PythonAnalyzer handles SyntaxError
# ==============================================================================
class TestPythonAnalyzerErrorHandling:
    def test_extract_imports_syntax_error(self, tmp_path):
        """Invalid Python file → extract_imports returns []."""
        g = _exec_visualize()
        PythonAnalyzer = g['PythonAnalyzer']
        f = tmp_path / 'bad.py'
        f.write_text('def (invalid syntax:\n', encoding='utf-8')
        analyzer = PythonAnalyzer()
        result = analyzer.extract_imports(f)
        assert result == []

    def test_extract_functions_syntax_error(self, tmp_path):
        """Invalid Python file → extract_functions_and_calls returns ({}, {})."""
        g = _exec_visualize()
        PythonAnalyzer = g['PythonAnalyzer']
        f = tmp_path / 'bad.py'
        f.write_text('def (invalid syntax:\n', encoding='utf-8')
        analyzer = PythonAnalyzer()
        func_registry, call_edges = analyzer.extract_functions_and_calls(f)
        assert func_registry == {}
        assert call_edges == {}


# ==============================================================================
# Test 5: _build_call_graph accepts analyzer param
# ==============================================================================
class TestBuildCallGraphAcceptsAnalyzer:
    def test_accepts_analyzer_param(self, tmp_path):
        """_build_call_graph can be called with an explicit analyzer=PythonAnalyzer()."""
        g = _exec_visualize()
        PythonAnalyzer = g['PythonAnalyzer']
        _build_call_graph = g['_build_call_graph']

        src = tmp_path / 'mod.py'
        src.write_text(
            'def foo():\n'
            '    bar()\n'
            '\n'
            'def bar():\n'
            '    pass\n',
            encoding='utf-8'
        )
        # Must not raise
        dest, content = _build_call_graph(
            tmp_path, [src], focus=None, entry=None, analyzer=PythonAnalyzer()
        )
        assert content.startswith('graph TD')


# ==============================================================================
# Test 6: _build_file_graph accepts analyzer param
# ==============================================================================
class TestBuildFileGraphAcceptsAnalyzer:
    def test_accepts_analyzer_param(self, tmp_path):
        """_build_file_graph can be called with an explicit analyzer=PythonAnalyzer()."""
        g = _exec_visualize()
        PythonAnalyzer = g['PythonAnalyzer']
        _scan_files = g['_scan_files']
        _build_file_graph = g['_build_file_graph']

        src = tmp_path / 'src'
        src.mkdir()
        (src / 'models.py').write_text('class Foo:\n    pass\n', encoding='utf-8')
        (src / 'service.py').write_text('from src.models import Foo\n', encoding='utf-8')

        all_files, module_index, file_to_node = _scan_files(tmp_path)
        # Must not raise
        dest, content = _build_file_graph(
            tmp_path, all_files, module_index, file_to_node, focus=None,
            analyzer=PythonAnalyzer()
        )
        assert content.startswith('graph TD')


# ==============================================================================
# Test 7: _scan_call_edges accepts analyzer param
# ==============================================================================
class TestScanCallEdgesAcceptsAnalyzer:
    def test_accepts_analyzer_param(self, tmp_path):
        """_scan_call_edges can be called with an explicit analyzer=PythonAnalyzer()."""
        g = _exec_visualize()
        PythonAnalyzer = g['PythonAnalyzer']
        _scan_call_edges = g['_scan_call_edges']

        src = tmp_path / 'mod.py'
        src.write_text('def foo():\n    pass\n', encoding='utf-8')

        # Must not raise
        func_registry, call_edges = _scan_call_edges(tmp_path, [src], analyzer=PythonAnalyzer())
        assert isinstance(func_registry, dict)
        assert isinstance(call_edges, dict)


# ==============================================================================
# Test 8: Default analyzer is PythonAnalyzer (backward compat)
# ==============================================================================
class TestDefaultAnalyzerIsBackwardCompat:
    def test_build_call_graph_no_analyzer(self, tmp_path):
        """_build_call_graph works without explicit analyzer param (default PythonAnalyzer)."""
        g = _exec_visualize()
        _build_call_graph = g['_build_call_graph']

        src = tmp_path / 'mod.py'
        src.write_text('def foo():\n    pass\n', encoding='utf-8')

        # No analyzer param — should work as before
        dest, content = _build_call_graph(tmp_path, [src], focus=None, entry=None)
        assert content.startswith('graph TD')

    def test_build_file_graph_no_analyzer(self, tmp_path):
        """_build_file_graph works without explicit analyzer param."""
        g = _exec_visualize()
        _scan_files = g['_scan_files']
        _build_file_graph = g['_build_file_graph']

        src = tmp_path / 'src'
        src.mkdir()
        (src / 'models.py').write_text('class Foo:\n    pass\n', encoding='utf-8')

        all_files, module_index, file_to_node = _scan_files(tmp_path)
        dest, content = _build_file_graph(
            tmp_path, all_files, module_index, file_to_node, focus=None
        )
        assert content.startswith('graph TD')

    def test_scan_call_edges_no_analyzer(self, tmp_path):
        """_scan_call_edges works without explicit analyzer param."""
        g = _exec_visualize()
        _scan_call_edges = g['_scan_call_edges']

        src = tmp_path / 'mod.py'
        src.write_text('def foo():\n    pass\n', encoding='utf-8')

        func_registry, call_edges = _scan_call_edges(tmp_path, [src])
        assert isinstance(func_registry, dict)


# ==============================================================================
# Test 9: Extensibility — DummyAnalyzer plugs into _build_call_graph
# ==============================================================================
class TestExtensibilityWithDummyAnalyzer:
    def test_dummy_analyzer_used_in_build_call_graph(self, tmp_path):
        """A custom LanguageAnalyzer can be passed to _build_call_graph."""
        g = _exec_visualize()
        LanguageAnalyzer = g['LanguageAnalyzer']
        _build_call_graph = g['_build_call_graph']

        class DummyAnalyzer(LanguageAnalyzer):
            def extract_imports(self, file_path):
                return []

            def extract_functions_and_calls(self, file_path):
                # Return hardcoded data regardless of file content
                func_registry = {
                    'dummy_func': 'dummy_module',
                    'helper_func': 'dummy_module',
                }
                call_edges = {
                    'dummy_func': ['helper_func'],
                    'helper_func': [],
                }
                return func_registry, call_edges

        # Create a dummy file (content doesn't matter — DummyAnalyzer ignores it)
        src = tmp_path / 'irrelevant.py'
        src.write_text('# no real code\n', encoding='utf-8')

        dummy = DummyAnalyzer()
        dest, content = _build_call_graph(
            tmp_path, [src], focus=None, entry=None, analyzer=dummy
        )
        # The graph should contain our dummy function names
        assert 'dummy_func' in content
        assert 'helper_func' in content

    def test_dummy_analyzer_used_in_scan_call_edges(self, tmp_path):
        """A custom LanguageAnalyzer is respected by _scan_call_edges."""
        g = _exec_visualize()
        LanguageAnalyzer = g['LanguageAnalyzer']
        _scan_call_edges = g['_scan_call_edges']

        class DummyAnalyzer(LanguageAnalyzer):
            def extract_imports(self, file_path):
                return []

            def extract_functions_and_calls(self, file_path):
                return {'dummy_scan_func': 'stem'}, {'dummy_scan_func': []}

        src = tmp_path / 'irrelevant.py'
        src.write_text('# no real code\n', encoding='utf-8')

        func_registry, call_edges = _scan_call_edges(tmp_path, [src], analyzer=DummyAnalyzer())
        assert 'dummy_scan_func' in func_registry
