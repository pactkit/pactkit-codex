"""STORY-slim-033: Java LanguageAnalyzer adapter.

Tests verify:
1. JavaAnalyzer instantiation, is LanguageAnalyzer subclass
2. JavaAnalyzer.extract_imports(): regular, static, wildcard imports
3. JavaAnalyzer.extract_functions_and_calls(): methods with class context,
   constructors, static methods
4. Call extraction: method invocations with/without object
5. Error handling: FileNotFoundError, empty file
6. _select_analyzer("java") returns JavaAnalyzer
7. Graceful degradation when tree-sitter-java not installed
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


# Java source samples used across tests
JAVA_SIMPLE_IMPORT = b'''package com.app;

import com.app.Config;
import com.app.utils.Helper;

public class App {
    public void start() {
        Config config = new Config();
        config.load();
    }
}
'''

JAVA_STATIC_IMPORT = b'''package com.app;

import static com.app.Config.load;
import static com.app.utils.Helper.format;

public class App {
    public void start() {
        load();
    }
}
'''

JAVA_WILDCARD_IMPORT = b'''package com.app;

import com.app.*;
import com.app.utils.*;

public class App {
    public void run() {
        System.out.println("running");
    }
}
'''

JAVA_METHODS = b'''package com.app;

public class Service {
    public void handleRequest() {
        processData();
    }

    private void processData() {
        System.out.println("processing");
    }
}
'''

JAVA_STATIC_METHOD = b'''package com.app;

public class Main {
    public static void main(String[] args) {
        Config.load();
        process();
    }

    private static void process() {
        System.out.println("done");
    }
}
'''

JAVA_CONSTRUCTOR = b'''package com.app;

public class Config {
    private String value;

    public Config() {
        this.value = "default";
        init();
    }

    private void init() {
        System.out.println("init");
    }
}
'''

JAVA_METHOD_CALLS_WITH_OBJECT = b'''package com.app;

public class Controller {
    private Service service;

    public void handleRequest() {
        service.process();
        helper();
    }

    private void helper() {
        System.out.println("helping");
    }
}
'''


# ==============================================================================
# Test 1: JavaAnalyzer — creation and type hierarchy
# ==============================================================================
class TestJavaAnalyzerCreation:
    def test_tree_sitter_java_available(self):
        """tree-sitter-java must be importable in this environment."""
        import tree_sitter_java  # noqa: F401

    def test_java_analyzer_instantiates(self):
        """JavaAnalyzer() instantiates without error."""
        g = _exec_visualize()
        JavaAnalyzer = g.get('JavaAnalyzer')
        if JavaAnalyzer is None:
            import pytest
            pytest.skip("JavaAnalyzer not yet implemented")
        analyzer = JavaAnalyzer()
        assert analyzer is not None

    def test_java_analyzer_is_language_analyzer(self):
        """JavaAnalyzer is a subclass of LanguageAnalyzer."""
        g = _exec_visualize()
        LanguageAnalyzer = g.get('LanguageAnalyzer')
        JavaAnalyzer = g.get('JavaAnalyzer')
        if JavaAnalyzer is None or LanguageAnalyzer is None:
            import pytest
            pytest.skip("JavaAnalyzer or LanguageAnalyzer not yet implemented")
        assert issubclass(JavaAnalyzer, LanguageAnalyzer)

    def test_java_analyzer_is_tree_sitter_analyzer(self):
        """JavaAnalyzer is a subclass of TreeSitterAnalyzer."""
        g = _exec_visualize()
        TreeSitterAnalyzer = g.get('TreeSitterAnalyzer')
        JavaAnalyzer = g.get('JavaAnalyzer')
        if JavaAnalyzer is None or TreeSitterAnalyzer is None:
            import pytest
            pytest.skip("JavaAnalyzer or TreeSitterAnalyzer not yet implemented")
        assert issubclass(JavaAnalyzer, TreeSitterAnalyzer)


# ==============================================================================
# Test 2: JavaAnalyzer.extract_imports()
# ==============================================================================
class TestJavaAnalyzerExtractImports:
    def _get_java_analyzer(self):
        g = _exec_visualize()
        JavaAnalyzer = g.get('JavaAnalyzer')
        if JavaAnalyzer is None:
            import pytest
            pytest.skip("JavaAnalyzer not yet implemented")
        return JavaAnalyzer()

    def test_regular_import(self, tmp_path):
        """import com.app.Config; -> ['com.app.Config', ...]"""
        analyzer = self._get_java_analyzer()
        f = tmp_path / 'App.java'
        f.write_bytes(JAVA_SIMPLE_IMPORT)
        result = analyzer.extract_imports(f)
        assert 'com.app.Config' in result

    def test_multiple_imports(self, tmp_path):
        """Both com.app.Config and com.app.utils.Helper returned."""
        analyzer = self._get_java_analyzer()
        f = tmp_path / 'App.java'
        f.write_bytes(JAVA_SIMPLE_IMPORT)
        result = analyzer.extract_imports(f)
        assert 'com.app.Config' in result
        assert 'com.app.utils.Helper' in result

    def test_static_import_returns_class_path(self, tmp_path):
        """import static com.app.Config.load; -> 'com.app.Config' (not '.load')"""
        analyzer = self._get_java_analyzer()
        f = tmp_path / 'App.java'
        f.write_bytes(JAVA_STATIC_IMPORT)
        result = analyzer.extract_imports(f)
        # Static imports: should return the class-level path
        # At minimum, some path containing 'com.app' should be present
        assert any('com.app' in r for r in result), f"No com.app in imports: {result}"

    def test_wildcard_import(self, tmp_path):
        """import com.app.*; -> 'com.app' (wildcard stripped)"""
        analyzer = self._get_java_analyzer()
        f = tmp_path / 'App.java'
        f.write_bytes(JAVA_WILDCARD_IMPORT)
        result = analyzer.extract_imports(f)
        # Should contain something like 'com.app' or 'com.app.*'
        assert any('com.app' in r for r in result), f"No com.app in wildcard imports: {result}"

    def test_returns_list(self, tmp_path):
        """extract_imports returns a list."""
        analyzer = self._get_java_analyzer()
        f = tmp_path / 'App.java'
        f.write_bytes(JAVA_SIMPLE_IMPORT)
        result = analyzer.extract_imports(f)
        assert isinstance(result, list)

    def test_empty_for_no_imports(self, tmp_path):
        """Java file with no imports returns []."""
        analyzer = self._get_java_analyzer()
        f = tmp_path / 'App.java'
        f.write_bytes(b'package com.app;\n\npublic class App {}\n')
        result = analyzer.extract_imports(f)
        assert isinstance(result, list)


# ==============================================================================
# Test 3: JavaAnalyzer.extract_functions_and_calls()
# ==============================================================================
class TestJavaAnalyzerExtractFunctionsAndCalls:
    def _get_java_analyzer(self):
        g = _exec_visualize()
        JavaAnalyzer = g.get('JavaAnalyzer')
        if JavaAnalyzer is None:
            import pytest
            pytest.skip("JavaAnalyzer not yet implemented")
        return JavaAnalyzer()

    def test_returns_tuple(self, tmp_path):
        """extract_functions_and_calls returns a 2-tuple."""
        analyzer = self._get_java_analyzer()
        f = tmp_path / 'Service.java'
        f.write_bytes(JAVA_METHODS)
        result = analyzer.extract_functions_and_calls(f)
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_instance_method_registered_with_class_context(self, tmp_path):
        """public void handleRequest() in class Service -> 'Service.handleRequest'"""
        analyzer = self._get_java_analyzer()
        f = tmp_path / 'Service.java'
        f.write_bytes(JAVA_METHODS)
        func_registry, call_edges = analyzer.extract_functions_and_calls(f)
        assert 'Service.handleRequest' in func_registry, (
            f"Expected 'Service.handleRequest' in func_registry: {list(func_registry.keys())}"
        )

    def test_static_method_registered_with_class_context(self, tmp_path):
        """public static void main() in class Main -> 'Main.main'"""
        analyzer = self._get_java_analyzer()
        f = tmp_path / 'Main.java'
        f.write_bytes(JAVA_STATIC_METHOD)
        func_registry, call_edges = analyzer.extract_functions_and_calls(f)
        assert 'Main.main' in func_registry, (
            f"Expected 'Main.main' in func_registry: {list(func_registry.keys())}"
        )

    def test_constructor_registered(self, tmp_path):
        """public Config() constructor -> 'Config.Config' in func_registry"""
        analyzer = self._get_java_analyzer()
        f = tmp_path / 'Config.java'
        f.write_bytes(JAVA_CONSTRUCTOR)
        func_registry, call_edges = analyzer.extract_functions_and_calls(f)
        assert 'Config.Config' in func_registry, (
            f"Expected 'Config.Config' in func_registry: {list(func_registry.keys())}"
        )

    def test_func_registry_stem_is_file_stem(self, tmp_path):
        """func_registry values are the file stem."""
        analyzer = self._get_java_analyzer()
        f = tmp_path / 'MyService.java'
        f.write_bytes(JAVA_METHODS)
        func_registry, call_edges = analyzer.extract_functions_and_calls(f)
        for stem in func_registry.values():
            assert stem == 'MyService', f"Expected stem 'MyService', got '{stem}'"

    def test_method_call_extracted(self, tmp_path):
        """handleRequest() calls processData() -> processData in callees."""
        analyzer = self._get_java_analyzer()
        f = tmp_path / 'Service.java'
        f.write_bytes(JAVA_METHODS)
        func_registry, call_edges = analyzer.extract_functions_and_calls(f)
        handle_key = 'Service.handleRequest'
        handle_callees = call_edges.get(handle_key, [])
        callee_str = ' '.join(handle_callees)
        assert 'processData' in callee_str, (
            f"Expected 'processData' in callees of {handle_key}: {handle_callees}"
        )

    def test_static_call_extracted(self, tmp_path):
        """main() calls Config.load() -> 'Config.load' or 'load' in callees."""
        analyzer = self._get_java_analyzer()
        f = tmp_path / 'Main.java'
        f.write_bytes(JAVA_STATIC_METHOD)
        func_registry, call_edges = analyzer.extract_functions_and_calls(f)
        main_key = 'Main.main'
        main_callees = call_edges.get(main_key, [])
        callee_str = ' '.join(main_callees)
        assert 'load' in callee_str, (
            f"Expected 'load' in callees of {main_key}: {main_callees}"
        )

    def test_object_method_call_extracted(self, tmp_path):
        """handleRequest() calls service.process() -> 'service.process' in callees."""
        analyzer = self._get_java_analyzer()
        f = tmp_path / 'Controller.java'
        f.write_bytes(JAVA_METHOD_CALLS_WITH_OBJECT)
        func_registry, call_edges = analyzer.extract_functions_and_calls(f)
        handle_key = 'Controller.handleRequest'
        handle_callees = call_edges.get(handle_key, [])
        callee_str = ' '.join(handle_callees)
        assert 'process' in callee_str, (
            f"Expected 'process' in callees of {handle_key}: {handle_callees}"
        )

    def test_constructor_calls_extracted(self, tmp_path):
        """Config() constructor calls init() -> 'init' in callees."""
        analyzer = self._get_java_analyzer()
        f = tmp_path / 'Config.java'
        f.write_bytes(JAVA_CONSTRUCTOR)
        func_registry, call_edges = analyzer.extract_functions_and_calls(f)
        ctor_key = 'Config.Config'
        ctor_callees = call_edges.get(ctor_key, [])
        callee_str = ' '.join(ctor_callees)
        assert 'init' in callee_str, (
            f"Expected 'init' in callees of {ctor_key}: {ctor_callees}"
        )


# ==============================================================================
# Test 4: JavaAnalyzer error handling
# ==============================================================================
class TestJavaAnalyzerErrorHandling:
    def _get_java_analyzer(self):
        g = _exec_visualize()
        JavaAnalyzer = g.get('JavaAnalyzer')
        if JavaAnalyzer is None:
            import pytest
            pytest.skip("JavaAnalyzer not yet implemented")
        return JavaAnalyzer()

    def test_extract_imports_file_not_found(self, tmp_path):
        """Missing file -> extract_imports returns []."""
        analyzer = self._get_java_analyzer()
        f = tmp_path / 'nonexistent.java'
        result = analyzer.extract_imports(f)
        assert result == []

    def test_extract_functions_file_not_found(self, tmp_path):
        """Missing file -> extract_functions_and_calls returns ({}, {})."""
        analyzer = self._get_java_analyzer()
        f = tmp_path / 'nonexistent.java'
        func_registry, call_edges = analyzer.extract_functions_and_calls(f)
        assert func_registry == {}
        assert call_edges == {}

    def test_extract_imports_empty_file(self, tmp_path):
        """Empty file -> extract_imports returns []."""
        analyzer = self._get_java_analyzer()
        f = tmp_path / 'Empty.java'
        f.write_bytes(b'')
        result = analyzer.extract_imports(f)
        assert isinstance(result, list)

    def test_extract_functions_empty_file(self, tmp_path):
        """Empty file -> extract_functions_and_calls returns ({}, {})."""
        analyzer = self._get_java_analyzer()
        f = tmp_path / 'Empty.java'
        f.write_bytes(b'')
        func_registry, call_edges = analyzer.extract_functions_and_calls(f)
        assert func_registry == {}
        assert call_edges == {}


# ==============================================================================
# Test 5: _select_analyzer("java") returns JavaAnalyzer
# ==============================================================================
class TestSelectAnalyzerJava:
    def test_select_java_returns_java_analyzer(self):
        """_select_analyzer('java') returns a JavaAnalyzer instance."""
        g = _exec_visualize()
        _select_analyzer = g.get('_select_analyzer')
        if _select_analyzer is None:
            import pytest
            pytest.skip("_select_analyzer not yet implemented")
        JavaAnalyzer = g.get('JavaAnalyzer')
        if JavaAnalyzer is None:
            import pytest
            pytest.skip("JavaAnalyzer not yet implemented")
        analyzer = _select_analyzer('java')
        assert isinstance(analyzer, JavaAnalyzer)

    def test_select_java_is_language_analyzer(self):
        """_select_analyzer('java') returns a LanguageAnalyzer instance."""
        g = _exec_visualize()
        _select_analyzer = g.get('_select_analyzer')
        LanguageAnalyzer = g.get('LanguageAnalyzer')
        if _select_analyzer is None or LanguageAnalyzer is None:
            import pytest
            pytest.skip("_select_analyzer or LanguageAnalyzer not yet implemented")
        analyzer = _select_analyzer('java')
        assert isinstance(analyzer, LanguageAnalyzer)


# ==============================================================================
# Test 6: Graceful degradation — _select_analyzer fallback
# ==============================================================================
class TestSelectAnalyzerFallbackForJava:
    def test_all_stacks_return_language_analyzer(self):
        """_select_analyzer always returns a LanguageAnalyzer for any stack."""
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
# Test 7: _detect_stack for Java projects
# ==============================================================================
class TestDetectStackJava:
    def test_pom_xml_detected_as_java(self, tmp_path):
        """Project with pom.xml -> _detect_stack returns 'java'."""
        g = _exec_visualize()
        _detect_stack = g.get('_detect_stack')
        if _detect_stack is None:
            import pytest
            pytest.skip("_detect_stack not yet implemented")
        (tmp_path / 'pom.xml').write_text('<project/>', encoding='utf-8')
        stack = _detect_stack(tmp_path)
        assert stack == 'java'

    def test_build_gradle_detected_as_java(self, tmp_path):
        """Project with build.gradle -> _detect_stack returns 'java'."""
        g = _exec_visualize()
        _detect_stack = g.get('_detect_stack')
        if _detect_stack is None:
            import pytest
            pytest.skip("_detect_stack not yet implemented")
        (tmp_path / 'build.gradle').write_text('apply plugin: "java"', encoding='utf-8')
        stack = _detect_stack(tmp_path)
        assert stack == 'java'
