"""Tests for STORY-slim-039: PDCA Sequence Parser."""
import textwrap


# ── _parse_pdca_sequence tests (R1) ──────────────────────────────────

class TestParsePdcaSequence:
    """Test _parse_pdca_sequence() extracts command→command sequence edges."""

    def _make_sprint_file(self, cmd_dir):
        """Create a minimal project-sprint.md with PDCA orchestration."""
        cmd_dir.mkdir(parents=True, exist_ok=True)
        (cmd_dir / 'project-sprint.md').write_text(textwrap.dedent("""\
            # Command: Sprint
            - **Agent**: Team Lead

            ## Phase 1: PDCA Execution

            ### Stage A: Build
            **A1** (`system-architect`): Execute `commands/project-plan.md`.
            **A2** (`senior-developer`): Execute `commands/project-act.md`.

            ### Stage B: Check
            - Launch `qa-engineer`: Execute `commands/project-check.md`.

            ### Stage C: Close
            - Launch `repo-maintainer`: Execute `commands/project-done.md`.
        """), encoding='utf-8')
        return cmd_dir

    def test_extracts_sequence_edges(self, tmp_path):
        from pactkit.skills.visualize import _parse_pdca_sequence, WorkflowGraph, WorkflowNode
        cmd_dir = self._make_sprint_file(tmp_path / 'commands')
        g = WorkflowGraph()
        # Pre-add command nodes (as _parse_commands would)
        for name in ['project-plan', 'project-act', 'project-check', 'project-done']:
            g.add_node(WorkflowNode(id=name, kind='command', label=name))
        _parse_pdca_sequence(cmd_dir, g)
        seq_edges = [e for e in g.edges if e.relation == 'sequence']
        assert len(seq_edges) >= 3
        sources = [(e.source, e.target) for e in seq_edges]
        assert ('project-plan', 'project-act') in sources
        assert ('project-act', 'project-check') in sources
        assert ('project-check', 'project-done') in sources

    def test_no_sprint_file_no_crash(self, tmp_path):
        from pactkit.skills.visualize import _parse_pdca_sequence, WorkflowGraph
        cmd_dir = tmp_path / 'commands'
        cmd_dir.mkdir()
        g = WorkflowGraph()
        _parse_pdca_sequence(cmd_dir, g)
        assert len(g.edges) == 0

    def test_nonexistent_dir_no_crash(self, tmp_path):
        from pactkit.skills.visualize import _parse_pdca_sequence, WorkflowGraph
        g = WorkflowGraph()
        _parse_pdca_sequence(tmp_path / 'nonexistent', g)
        assert len(g.edges) == 0

    def test_only_creates_edges_for_existing_nodes(self, tmp_path):
        from pactkit.skills.visualize import _parse_pdca_sequence, WorkflowGraph, WorkflowNode
        cmd_dir = self._make_sprint_file(tmp_path / 'commands')
        g = WorkflowGraph()
        # Only add plan and act, not check/done
        g.add_node(WorkflowNode(id='project-plan', kind='command', label='project-plan'))
        g.add_node(WorkflowNode(id='project-act', kind='command', label='project-act'))
        _parse_pdca_sequence(cmd_dir, g)
        seq_edges = [e for e in g.edges if e.relation == 'sequence']
        # Only plan→act should exist (check/done not in graph)
        assert len(seq_edges) == 1
        assert seq_edges[0].source == 'project-plan'
        assert seq_edges[0].target == 'project-act'


# ── Dashed edge rendering tests (R2, R3) ─────────────────────────────

class TestSequenceEdgeRendering:
    """Test to_mermaid() renders sequence edges as dashed arrows."""

    def test_sequence_edge_dashed(self):
        from pactkit.skills.visualize import WorkflowNode, WorkflowEdge, WorkflowGraph
        g = WorkflowGraph()
        g.add_node(WorkflowNode(id='cmd-a', kind='command', label='A'))
        g.add_node(WorkflowNode(id='cmd-b', kind='command', label='B'))
        g.add_edge(WorkflowEdge(source='cmd-a', target='cmd-b', relation='sequence'))
        mmd = g.to_mermaid()
        assert '-.->|sequence|' in mmd

    def test_invokes_edge_solid(self):
        from pactkit.skills.visualize import WorkflowNode, WorkflowEdge, WorkflowGraph
        g = WorkflowGraph()
        g.add_node(WorkflowNode(id='cmd-a', kind='command', label='A'))
        g.add_node(WorkflowNode(id='agent-x', kind='agent', label='X'))
        g.add_edge(WorkflowEdge(source='cmd-a', target='agent-x', relation='invokes'))
        mmd = g.to_mermaid()
        assert '-->|invokes|' in mmd
        assert '-.->|invokes|' not in mmd

    def test_mixed_edges(self):
        from pactkit.skills.visualize import WorkflowNode, WorkflowEdge, WorkflowGraph
        g = WorkflowGraph()
        g.add_node(WorkflowNode(id='cmd-a', kind='command', label='A'))
        g.add_node(WorkflowNode(id='cmd-b', kind='command', label='B'))
        g.add_node(WorkflowNode(id='agent-x', kind='agent', label='X'))
        g.add_edge(WorkflowEdge(source='cmd-a', target='cmd-b', relation='sequence'))
        g.add_edge(WorkflowEdge(source='cmd-a', target='agent-x', relation='invokes'))
        mmd = g.to_mermaid()
        assert '-.->|sequence|' in mmd
        assert '-->|invokes|' in mmd


# ── Integration test (R4) ────────────────────────────────────────────

class TestSequenceInBuildWorkflowGraph:
    """Test that build_workflow_graph includes sequence edges."""

    def test_build_includes_sequence_edges(self, tmp_path):
        from pactkit.skills.visualize import build_workflow_graph
        cmd_dir = tmp_path / 'commands'
        cmd_dir.mkdir()
        # Create commands that _parse_commands will find
        for name in ['project-plan', 'project-act', 'project-check', 'project-done']:
            (cmd_dir / f'{name}.md').write_text(textwrap.dedent(f"""\
                # Command: {name.split('-')[1].title()}
                - **Agent**: Some Role
            """), encoding='utf-8')
        # Create sprint file with PDCA sequence
        (cmd_dir / 'project-sprint.md').write_text(textwrap.dedent("""\
            # Command: Sprint
            ## Phase 1: PDCA Execution
            ### Stage A: Build
            **A1**: Execute `commands/project-plan.md`.
            **A2**: Execute `commands/project-act.md`.
            ### Stage B: Check
            Execute `commands/project-check.md`.
            ### Stage C: Close
            Execute `commands/project-done.md`.
        """), encoding='utf-8')
        rules_dir = tmp_path / 'rules'
        rules_dir.mkdir()
        skills_dir = tmp_path / 'skills'
        skills_dir.mkdir()
        g = build_workflow_graph(commands_dir=cmd_dir, rules_dir=rules_dir, skills_dir=skills_dir)
        seq_edges = [e for e in g.edges if e.relation == 'sequence']
        assert len(seq_edges) >= 3


# ── Backward compatibility (R5) ──────────────────────────────────────

class TestBackwardCompatibility:
    """Existing edge types must not change rendering."""

    def test_no_sequence_graph_unchanged(self):
        from pactkit.skills.visualize import WorkflowNode, WorkflowEdge, WorkflowGraph
        g = WorkflowGraph()
        g.add_node(WorkflowNode(id='cmd-a', kind='command', label='A'))
        g.add_node(WorkflowNode(id='skill-b', kind='skill', label='B'))
        g.add_edge(WorkflowEdge(source='cmd-a', target='skill-b', relation='invokes'))
        mmd = g.to_mermaid()
        # No dashed arrows when there are no sequence edges
        assert '-.->' not in mmd
        assert '-->|invokes|' in mmd
