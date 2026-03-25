"""Tests for STORY-038: Add call_graph.mmd to standard PDCA update cycle.

AC1: Act Phase 4 "Update Reality" includes --mode call
AC2: Done Phase 2 "Update Reality" includes --mode call
AC3: Focus graph output uses mode-specific filenames
"""
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


def _prompts():
    import importlib

    import pactkit.prompts as p
    importlib.reload(p)
    return p


# ==============================================================================
# AC1: Act Phase 4 "Update Reality" includes --mode call
# ==============================================================================
class TestAC1ActUpdatesCallGraph:

    def test_act_update_reality_has_mode_call(self):
        """Act Phase 4 must include visualize --mode call."""
        p = _prompts()
        act = p.COMMANDS_CONTENT['project-act.md']
        # Must have --mode call in the Update Reality section
        assert '--mode call' in act

    def test_act_call_graph_after_class(self):
        """--mode call must appear AFTER --mode class in Act."""
        p = _prompts()
        act = p.COMMANDS_CONTENT['project-act.md']
        class_pos = act.find('--mode class')
        call_pos = act.rfind('--mode call')
        assert class_pos < call_pos, "call graph update must come after class graph"


# ==============================================================================
# AC2: Done Phase 2 "Update Reality" includes --mode call
# ==============================================================================
class TestAC2DoneUpdatesCallGraph:

    def test_done_update_reality_has_mode_call(self):
        """Done Phase 2 must include visualize --mode call."""
        p = _prompts()
        done = p.COMMANDS_CONTENT['project-done.md']
        assert '--mode call' in done

    def test_done_call_graph_after_class(self):
        """--mode call must appear AFTER --mode class in Done."""
        p = _prompts()
        done = p.COMMANDS_CONTENT['project-done.md']
        class_pos = done.find('--mode class')
        call_pos = done.rfind('--mode call')
        assert class_pos < call_pos, "call graph update must come after class graph"


# ==============================================================================
# AC3: Focus graph output uses mode-specific filenames
# ==============================================================================
class TestAC3FocusGraphModeSpecific:

    def test_file_mode_focus_output(self):
        """File mode with --focus should output focus_file_graph.mmd."""
        from pactkit.skills.visualize import _build_file_graph
        root = Path('/fake/root')
        fake_file = root / 'src' / 'auth.py'
        file_to_node = {fake_file: 'auth_py'}
        dest, _ = _build_file_graph(root, [], {}, file_to_node, focus='auth')
        assert 'focus_file_graph.mmd' in str(dest)

    def test_class_mode_focus_output(self):
        """Class mode with --focus should output focus_class_graph.mmd."""
        from pactkit.skills.visualize import _build_class_graph
        root = Path('/fake/root')
        dest, _ = _build_class_graph(root, [], focus='auth')
        assert 'focus_class_graph.mmd' in str(dest)

    def test_call_mode_focus_output(self):
        """Call mode with --focus should output focus_call_graph.mmd."""
        from pactkit.skills.visualize import _build_call_graph
        root = Path('/fake/root')
        dest, _ = _build_call_graph(root, [], focus='auth', entry=None)
        assert 'focus_call_graph.mmd' in str(dest)

    def test_no_collision_between_modes(self):
        """Each mode must produce a distinct focus filename."""
        from pactkit.skills.visualize import (
            _build_call_graph,
            _build_class_graph,
            _build_file_graph,
        )
        root = Path('/fake/root')
        fake_file = root / 'src' / 'auth.py'
        file_to_node = {fake_file: 'auth_py'}
        d1, _ = _build_file_graph(root, [], {}, file_to_node, focus='auth')
        d2, _ = _build_class_graph(root, [], focus='auth')
        d3, _ = _build_call_graph(root, [], focus='auth', entry=None)
        names = {d1.name, d2.name, d3.name}
        assert len(names) == 3, f"Collision: {names}"


# ==============================================================================
# AC3 supplementary: prompt template references updated
# ==============================================================================
class TestAC3PromptReferences:

    def test_skill_prompt_lists_mode_specific_focus(self):
        """Visualize skill prompt should document mode-specific focus filenames."""
        p = _prompts()
        skill = p.SKILL_VISUALIZE_MD
        # Should mention at least one mode-specific focus filename
        assert ('focus_file_graph' in skill or
                'focus_class_graph' in skill or
                'focus_call_graph' in skill)


# ==============================================================================
# Backward compat: non-focus mode paths unchanged
# ==============================================================================
class TestBackwardCompat:

    def test_file_mode_default_output_unchanged(self):
        from pactkit.skills.visualize import _build_file_graph
        root = Path('/fake/root')
        dest, _ = _build_file_graph(root, [], {}, {}, focus=None)
        assert dest.name == 'code_graph.mmd'

    def test_class_mode_default_output_unchanged(self):
        from pactkit.skills.visualize import _build_class_graph
        root = Path('/fake/root')
        dest, _ = _build_class_graph(root, [], focus=None)
        assert dest.name == 'class_graph.mmd'

    def test_call_mode_default_output_unchanged(self):
        from pactkit.skills.visualize import _build_call_graph
        root = Path('/fake/root')
        dest, _ = _build_call_graph(root, [], focus=None, entry=None)
        assert dest.name == 'call_graph.mmd'
