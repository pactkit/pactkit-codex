"""Tests for STORY-slim-037: Workflow Impact Analysis."""
import textwrap


# ── reverse_reach tests (R1) ─────────────────────────────────────────

class TestReverseReach:
    """Test WorkflowGraph.reverse_reach() for backward traversal."""

    def _make_graph(self):
        from pactkit.skills.visualize import WorkflowNode, WorkflowEdge, WorkflowGraph
        g = WorkflowGraph()
        # command-A → skill-B → file-C
        g.add_node(WorkflowNode(id='cmd-A', kind='command', label='A'))
        g.add_node(WorkflowNode(id='skill-B', kind='skill', label='B'))
        g.add_node(WorkflowNode(id='file-C', kind='file', label='C'))
        g.add_edge(WorkflowEdge(source='cmd-A', target='skill-B', relation='depends_on'))
        g.add_edge(WorkflowEdge(source='skill-B', target='file-C', relation='contains'))
        return g

    def test_reverse_reach_from_leaf(self):
        g = self._make_graph()
        reached = g.reverse_reach('file-C')
        assert 'file-C' in reached
        assert 'skill-B' in reached
        assert 'cmd-A' in reached

    def test_reverse_reach_from_middle(self):
        g = self._make_graph()
        reached = g.reverse_reach('skill-B')
        assert 'skill-B' in reached
        assert 'cmd-A' in reached
        assert 'file-C' not in reached

    def test_reverse_reach_from_root(self):
        g = self._make_graph()
        reached = g.reverse_reach('cmd-A')
        assert reached == {'cmd-A'}

    def test_reverse_reach_nonexistent_node(self):
        g = self._make_graph()
        reached = g.reverse_reach('nonexistent')
        assert reached == {'nonexistent'}  # only self

    def test_reverse_reach_diamond(self):
        """Test diamond pattern: cmd1→skill, cmd2→skill, skill→file."""
        from pactkit.skills.visualize import WorkflowNode, WorkflowEdge, WorkflowGraph
        g = WorkflowGraph()
        g.add_node(WorkflowNode(id='cmd1', kind='command', label='C1'))
        g.add_node(WorkflowNode(id='cmd2', kind='command', label='C2'))
        g.add_node(WorkflowNode(id='skill', kind='skill', label='S'))
        g.add_node(WorkflowNode(id='file', kind='file', label='F'))
        g.add_edge(WorkflowEdge(source='cmd1', target='skill', relation='depends_on'))
        g.add_edge(WorkflowEdge(source='cmd2', target='skill', relation='depends_on'))
        g.add_edge(WorkflowEdge(source='skill', target='file', relation='contains'))
        reached = g.reverse_reach('file')
        assert reached == {'file', 'skill', 'cmd1', 'cmd2'}


# ── impact --mode workflow tests (R2, R3) ────────────────────────────

def _setup_pactkit_tree(tmp_path):
    """Create minimal PactKit directory for workflow impact tests."""
    cmd_dir = tmp_path / '.claude' / 'commands'
    cmd_dir.mkdir(parents=True)
    (cmd_dir / 'project-act.md').write_text(textwrap.dedent("""\
        # Command: Act
        - **Agent**: Senior Developer
        Use pactkit-board for board updates.
        Use pactkit-trace skill.
    """), encoding='utf-8')
    (cmd_dir / 'project-done.md').write_text(textwrap.dedent("""\
        # Command: Done
        - **Agent**: Repo Maintainer
        Use pactkit-board to archive.
        Use pactkit-visualize for graphs.
    """), encoding='utf-8')

    rules_dir = tmp_path / '.claude' / 'rules'
    rules_dir.mkdir(parents=True)
    (rules_dir / '04-routing-table.md').write_text(textwrap.dedent("""\
        # Command Reference (Routing Table)
        ## Commands (2 entry points)
        ### Act (`/project-act`)
        - **Role**: Senior Developer
        - **Playbook**: `commands/project-act.md`
        ### Done (`/project-done`)
        - **Role**: Repo Maintainer
        - **Playbook**: `commands/project-done.md`
    """), encoding='utf-8')

    skills_dir = tmp_path / '.claude' / 'skills'
    (skills_dir / 'pactkit-board' / 'scripts').mkdir(parents=True)
    (skills_dir / 'pactkit-board' / 'scripts' / 'board.py').write_text('# board', encoding='utf-8')
    (skills_dir / 'pactkit-trace' / 'scripts').mkdir(parents=True)
    (skills_dir / 'pactkit-trace' / 'scripts' / 'trace.py').write_text('# trace', encoding='utf-8')
    (skills_dir / 'pactkit-visualize' / 'scripts').mkdir(parents=True)
    (skills_dir / 'pactkit-visualize' / 'scripts' / 'visualize.py').write_text('# viz', encoding='utf-8')

    (tmp_path / 'pyproject.toml').write_text('[project]\nname = "test"', encoding='utf-8')
    return tmp_path


class TestWorkflowImpact:
    """Test impact() with mode='workflow'."""

    def test_impact_finds_affected_commands(self, tmp_path):
        from pactkit.skills.visualize import workflow_impact
        root = _setup_pactkit_tree(tmp_path)
        result = workflow_impact(target=str(root), entry='pactkit-board')
        assert 'project-act' in result
        assert 'project-done' in result

    def test_impact_output_format(self, tmp_path):
        from pactkit.skills.visualize import workflow_impact
        root = _setup_pactkit_tree(tmp_path)
        result = workflow_impact(target=str(root), entry='pactkit-board')
        assert 'Workflow Impact' in result
        assert 'Commands:' in result

    def test_impact_invalid_entry(self, tmp_path):
        from pactkit.skills.visualize import workflow_impact
        root = _setup_pactkit_tree(tmp_path)
        result = workflow_impact(target=str(root), entry='nonexistent-skill')
        assert 'not found' in result.lower() or 'available' in result.lower()

    def test_impact_multiple_entries(self, tmp_path):
        from pactkit.skills.visualize import workflow_impact
        root = _setup_pactkit_tree(tmp_path)
        result = workflow_impact(target=str(root), entries=['pactkit-board', 'pactkit-trace'])
        assert 'project-act' in result

    def test_impact_groups_by_kind(self, tmp_path):
        from pactkit.skills.visualize import workflow_impact
        root = _setup_pactkit_tree(tmp_path)
        result = workflow_impact(target=str(root), entry='pactkit-board')
        # Should have kind groupings
        lines = result.split('\n')
        kind_lines = [l for l in lines if any(k in l for k in ['Commands:', 'Agents:', 'Skills:', 'Files:'])]
        assert len(kind_lines) >= 1
