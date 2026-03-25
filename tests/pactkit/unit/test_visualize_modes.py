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


def _create_test_project(tmp_path):
    """Create a minimal Python project for testing."""
    src = tmp_path / 'src'
    src.mkdir()
    (src / '__init__.py').write_text('', encoding='utf-8')

    (src / 'models.py').write_text(
        'class Animal:\n'
        '    def speak(self):\n'
        '        return "..."\n'
        '\n'
        'class Dog(Animal):\n'
        '    def speak(self):\n'
        '        return self.bark()\n'
        '\n'
        '    def bark(self):\n'
        '        return "woof"\n',
        encoding='utf-8'
    )

    (src / 'service.py').write_text(
        'from src.models import Dog\n'
        '\n'
        'def create_dog():\n'
        '    return Dog()\n'
        '\n'
        'def process():\n'
        '    dog = create_dog()\n'
        '    return dog.speak()\n',
        encoding='utf-8'
    )

    (src / 'main.py').write_text(
        'from src.service import process\n'
        '\n'
        'def run():\n'
        '    result = process()\n'
        '    return result\n'
        '\n'
        'def helper():\n'
        '    pass\n',
        encoding='utf-8'
    )
    return tmp_path


# ==============================================================================
# Scenario 6: Default mode unchanged
# ==============================================================================
class TestDefaultModeUnchanged:
    def test_default_mode_produces_graph_td(self, tmp_path):
        proj = _create_test_project(tmp_path)
        g = _exec_visualize()
        result = g['visualize'](str(proj))
        output = (proj / 'docs/architecture/graphs/code_graph.mmd').read_text()
        assert output.startswith('graph TD')

    def test_default_mode_file_explicit(self, tmp_path):
        proj = _create_test_project(tmp_path)
        g = _exec_visualize()
        result = g['visualize'](str(proj), mode='file')
        assert 'code_graph.mmd' in result


# ==============================================================================
# Scenario 1: Class mode basic output
# ==============================================================================
class TestClassMode:
    def test_class_mode_outputs_classdiagram(self, tmp_path):
        proj = _create_test_project(tmp_path)
        g = _exec_visualize()
        result = g['visualize'](str(proj), mode='class')
        output = (proj / 'docs/architecture/graphs/class_graph.mmd').read_text()
        assert 'classDiagram' in output

    def test_class_mode_contains_class_names(self, tmp_path):
        proj = _create_test_project(tmp_path)
        g = _exec_visualize()
        g['visualize'](str(proj), mode='class')
        output = (proj / 'docs/architecture/graphs/class_graph.mmd').read_text()
        assert 'Animal' in output
        assert 'Dog' in output

    def test_class_mode_contains_methods(self, tmp_path):
        proj = _create_test_project(tmp_path)
        g = _exec_visualize()
        g['visualize'](str(proj), mode='class')
        output = (proj / 'docs/architecture/graphs/class_graph.mmd').read_text()
        assert 'speak' in output
        assert 'bark' in output


# ==============================================================================
# Scenario 2: Inheritance
# ==============================================================================
class TestInheritance:
    def test_inheritance_rendered(self, tmp_path):
        proj = _create_test_project(tmp_path)
        g = _exec_visualize()
        g['visualize'](str(proj), mode='class')
        output = (proj / 'docs/architecture/graphs/class_graph.mmd').read_text()
        assert 'Animal <|-- Dog' in output


# ==============================================================================
# Scenario 3: Call mode direct calls
# ==============================================================================
class TestCallModeDirect:
    def test_call_mode_outputs_graph_td(self, tmp_path):
        proj = _create_test_project(tmp_path)
        g = _exec_visualize()
        result = g['visualize'](str(proj), mode='call')
        output = (proj / 'docs/architecture/graphs/call_graph.mmd').read_text()
        assert output.startswith('graph TD')

    def test_call_mode_contains_direct_calls(self, tmp_path):
        proj = _create_test_project(tmp_path)
        g = _exec_visualize()
        g['visualize'](str(proj), mode='call')
        output = (proj / 'docs/architecture/graphs/call_graph.mmd').read_text()
        # process() calls create_dog()
        assert 'process' in output
        assert 'create_dog' in output


# ==============================================================================
# Scenario 4: Transitive chain (A→B→C)
# ==============================================================================
class TestTransitiveChain:
    def test_entry_finds_transitive_callees(self, tmp_path):
        proj = _create_test_project(tmp_path)
        g = _exec_visualize()
        g['visualize'](str(proj), mode='call', entry='run')
        output = (proj / 'docs/architecture/graphs/call_graph.mmd').read_text()
        # run → process → create_dog (transitive)
        assert 'run' in output
        assert 'process' in output
        assert 'create_dog' in output


# ==============================================================================
# Scenario 5: self method resolution
# ==============================================================================
class TestSelfMethodResolution:
    def test_self_call_resolved(self, tmp_path):
        proj = _create_test_project(tmp_path)
        g = _exec_visualize()
        g['visualize'](str(proj), mode='call')
        output = (proj / 'docs/architecture/graphs/call_graph.mmd').read_text()
        # Dog.speak() calls self.bark() → should show Dog.speak --> Dog.bark
        assert 'bark' in output


# ==============================================================================
# Scenario 7: BFS depth
# ==============================================================================
class TestBFSDepth:
    def test_four_level_chain(self, tmp_path):
        """a → b → c → d, all 4 nodes reachable from entry=a"""
        src = tmp_path / 'chain'
        src.mkdir()
        (src / 'deep.py').write_text(
            'def a():\n'
            '    b()\n'
            '\n'
            'def b():\n'
            '    c()\n'
            '\n'
            'def c():\n'
            '    d()\n'
            '\n'
            'def d():\n'
            '    pass\n',
            encoding='utf-8'
        )
        g = _exec_visualize()
        g['visualize'](str(tmp_path), mode='call', entry='a')
        output = (tmp_path / 'docs/architecture/graphs/call_graph.mmd').read_text()
        for fn in ['a', 'b', 'c', 'd']:
            assert fn in output, f'Function {fn} not found in transitive chain'


# ==============================================================================
# CLI parameter tests
# ==============================================================================
class TestCLIParameters:
    def test_visualize_accepts_mode_param(self):
        g = _exec_visualize()
        import inspect
        sig = inspect.signature(g['visualize'])
        assert 'mode' in sig.parameters

    def test_visualize_accepts_entry_param(self):
        g = _exec_visualize()
        import inspect
        sig = inspect.signature(g['visualize'])
        assert 'entry' in sig.parameters

    def test_mode_default_is_file(self):
        g = _exec_visualize()
        import inspect
        sig = inspect.signature(g['visualize'])
        assert sig.parameters['mode'].default == 'file'
