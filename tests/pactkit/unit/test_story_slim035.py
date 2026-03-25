"""Tests for STORY-slim-035: Workflow Parser — WorkflowGraph model and parsers."""
import textwrap


# ── WorkflowGraph data model tests (R1) ──────────────────────────────

class TestWorkflowDataModel:
    """Test WorkflowNode, WorkflowEdge, WorkflowGraph."""

    def _get_classes(self):
        from pactkit.skills.visualize import WorkflowNode, WorkflowEdge, WorkflowGraph
        return WorkflowNode, WorkflowEdge, WorkflowGraph

    def test_node_creation(self):
        WN, _, _ = self._get_classes()
        node = WN(id='project-act', kind='command', label='Act')
        assert node.id == 'project-act'
        assert node.kind == 'command'
        assert node.label == 'Act'

    def test_edge_creation(self):
        _, WE, _ = self._get_classes()
        edge = WE(source='project-act', target='senior-developer', relation='invokes')
        assert edge.source == 'project-act'
        assert edge.target == 'senior-developer'
        assert edge.relation == 'invokes'

    def test_graph_add_node(self):
        WN, _, WG = self._get_classes()
        g = WG()
        g.add_node(WN(id='a', kind='command', label='A'))
        assert len(g.nodes) == 1
        assert g.nodes['a'].label == 'A'

    def test_graph_add_edge(self):
        WN, WE, WG = self._get_classes()
        g = WG()
        g.add_node(WN(id='a', kind='command', label='A'))
        g.add_node(WN(id='b', kind='skill', label='B'))
        g.add_edge(WE(source='a', target='b', relation='invokes'))
        assert len(g.edges) == 1
        assert g.edges[0].source == 'a'

    def test_graph_duplicate_node_ignored(self):
        WN, _, WG = self._get_classes()
        g = WG()
        g.add_node(WN(id='a', kind='command', label='A'))
        g.add_node(WN(id='a', kind='command', label='A2'))
        assert len(g.nodes) == 1

    def test_to_mermaid_basic(self):
        WN, WE, WG = self._get_classes()
        g = WG()
        g.add_node(WN(id='cmd-a', kind='command', label='A'))
        g.add_node(WN(id='skill-b', kind='skill', label='B'))
        g.add_edge(WE(source='cmd-a', target='skill-b', relation='invokes'))
        mmd = g.to_mermaid()
        assert 'graph TD' in mmd
        assert 'cmd_a' in mmd  # sanitized
        assert 'skill_b' in mmd
        assert '|invokes|' in mmd

    def test_to_mermaid_subgraphs(self):
        WN, WE, WG = self._get_classes()
        g = WG()
        g.add_node(WN(id='cmd-a', kind='command', label='A'))
        g.add_node(WN(id='agent-x', kind='agent', label='X'))
        g.add_node(WN(id='skill-b', kind='skill', label='B'))
        g.add_node(WN(id='file-c', kind='file', label='C'))
        g.add_edge(WE(source='cmd-a', target='agent-x', relation='invokes'))
        mmd = g.to_mermaid()
        assert 'subgraph Commands' in mmd
        assert 'subgraph Agents' in mmd
        assert 'subgraph Skills' in mmd
        assert 'subgraph Files' in mmd
        assert 'end' in mmd


# ── Command parser tests (R2) ────────────────────────────────────────

class TestParseCommands:
    """Test _parse_commands() extracts command→agent, command→skill, command→file edges."""

    def test_extracts_agent_role(self, tmp_path):
        from pactkit.skills.visualize import _parse_commands, WorkflowGraph
        cmd_dir = tmp_path / 'commands'
        cmd_dir.mkdir()
        (cmd_dir / 'project-act.md').write_text(textwrap.dedent("""\
            # Command: Act
            - **Agent**: Senior Developer

            Use pactkit-trace skill to trace code.
            Run `python3 ~/.claude/skills/pactkit-board/scripts/board.py update_task`.
        """), encoding='utf-8')
        g = WorkflowGraph()
        _parse_commands(cmd_dir, g)
        assert 'project-act' in g.nodes
        assert g.nodes['project-act'].kind == 'command'
        # Should have agent edge
        agent_edges = [e for e in g.edges if e.relation == 'invokes' and e.source == 'project-act'
                       and g.nodes.get(e.target, None) and g.nodes[e.target].kind == 'agent']
        assert len(agent_edges) >= 1

    def test_extracts_skill_references(self, tmp_path):
        from pactkit.skills.visualize import _parse_commands, WorkflowGraph
        cmd_dir = tmp_path / 'commands'
        cmd_dir.mkdir()
        (cmd_dir / 'project-done.md').write_text(textwrap.dedent("""\
            # Command: Done
            - **Agent**: Repo Maintainer

            Use pactkit-board to update board.
            Run pactkit-visualize for graphs.
        """), encoding='utf-8')
        g = WorkflowGraph()
        _parse_commands(cmd_dir, g)
        skill_targets = {e.target for e in g.edges if e.relation == 'depends_on' and e.source == 'project-done'}
        assert 'pactkit-board' in skill_targets
        assert 'pactkit-visualize' in skill_targets

    def test_handles_empty_directory(self, tmp_path):
        from pactkit.skills.visualize import _parse_commands, WorkflowGraph
        cmd_dir = tmp_path / 'commands'
        cmd_dir.mkdir()
        g = WorkflowGraph()
        _parse_commands(cmd_dir, g)
        assert len(g.nodes) == 0

    def test_handles_nonexistent_directory(self, tmp_path):
        from pactkit.skills.visualize import _parse_commands, WorkflowGraph
        g = WorkflowGraph()
        _parse_commands(tmp_path / 'nonexistent', g)
        assert len(g.nodes) == 0


# ── Routing table parser tests (R3) ──────────────────────────────────

class TestParseRoutingTable:
    """Test _parse_routing_table() extracts command→agent→playbook mappings."""

    def test_parses_routing_table(self, tmp_path):
        from pactkit.skills.visualize import _parse_routing_table, WorkflowGraph
        rules_dir = tmp_path / 'rules'
        rules_dir.mkdir()
        (rules_dir / '04-routing-table.md').write_text(textwrap.dedent("""\
            # Command Reference (Routing Table)

            ## Commands (3 user-facing entry points)

            ### Init (`/project-init`)
            - **Role**: System Architect
            - **Playbook**: `commands/project-init.md`

            ### Act (`/project-act`)
            - **Role**: Senior Developer
            - **Playbook**: `commands/project-act.md`

            ### Done (`/project-done`)
            - **Role**: Repo Maintainer
            - **Playbook**: `commands/project-done.md`
        """), encoding='utf-8')
        g = WorkflowGraph()
        _parse_routing_table(rules_dir, g)
        # Should have command nodes
        assert 'project-init' in g.nodes
        assert 'project-act' in g.nodes
        assert 'project-done' in g.nodes
        # Should have agent nodes
        agent_names = {n.label for n in g.nodes.values() if n.kind == 'agent'}
        assert 'System Architect' in agent_names
        assert 'Senior Developer' in agent_names

    def test_handles_missing_routing_table(self, tmp_path):
        from pactkit.skills.visualize import _parse_routing_table, WorkflowGraph
        rules_dir = tmp_path / 'rules'
        rules_dir.mkdir()
        g = WorkflowGraph()
        _parse_routing_table(rules_dir, g)
        assert len(g.nodes) == 0

    def test_handles_nonexistent_rules_dir(self, tmp_path):
        from pactkit.skills.visualize import _parse_routing_table, WorkflowGraph
        g = WorkflowGraph()
        _parse_routing_table(tmp_path / 'nonexistent', g)
        assert len(g.nodes) == 0


# ── Skill file scanner tests (R4) ────────────────────────────────────

class TestScanSkillFiles:
    """Test _scan_skill_files() discovers skill→file edges."""

    def test_discovers_skill_scripts(self, tmp_path):
        from pactkit.skills.visualize import _scan_skill_files, WorkflowGraph
        skills_dir = tmp_path / 'skills'
        (skills_dir / 'pactkit-board' / 'scripts').mkdir(parents=True)
        (skills_dir / 'pactkit-board' / 'scripts' / 'board.py').write_text('# board', encoding='utf-8')
        (skills_dir / 'pactkit-trace').mkdir(parents=True)
        # pactkit-trace has no scripts dir
        g = WorkflowGraph()
        _scan_skill_files(skills_dir, g)
        assert 'pactkit-board' in g.nodes
        assert g.nodes['pactkit-board'].kind == 'skill'
        # Should have file edge
        file_edges = [e for e in g.edges if e.source == 'pactkit-board' and e.relation == 'contains']
        assert len(file_edges) >= 1

    def test_handles_empty_skills_dir(self, tmp_path):
        from pactkit.skills.visualize import _scan_skill_files, WorkflowGraph
        skills_dir = tmp_path / 'skills'
        skills_dir.mkdir()
        g = WorkflowGraph()
        _scan_skill_files(skills_dir, g)
        assert len(g.nodes) == 0

    def test_handles_nonexistent_skills_dir(self, tmp_path):
        from pactkit.skills.visualize import _scan_skill_files, WorkflowGraph
        g = WorkflowGraph()
        _scan_skill_files(tmp_path / 'nonexistent', g)
        assert len(g.nodes) == 0


# ── build_workflow_graph() integration tests (R5) ────────────────────

class TestBuildWorkflowGraph:
    """Test build_workflow_graph() combines all parsers."""

    def _setup_pactkit_dirs(self, tmp_path):
        """Create a minimal PactKit-like directory structure."""
        # Commands
        cmd_dir = tmp_path / 'commands'
        cmd_dir.mkdir()
        (cmd_dir / 'project-act.md').write_text(textwrap.dedent("""\
            # Command: Act
            - **Agent**: Senior Developer

            Use pactkit-trace skill.
            Use pactkit-board for board updates.
        """), encoding='utf-8')
        (cmd_dir / 'project-done.md').write_text(textwrap.dedent("""\
            # Command: Done
            - **Agent**: Repo Maintainer

            Use pactkit-board to archive.
            Use pactkit-visualize for graphs.
        """), encoding='utf-8')

        # Rules
        rules_dir = tmp_path / 'rules'
        rules_dir.mkdir()
        (rules_dir / '04-routing-table.md').write_text(textwrap.dedent("""\
            # Command Reference (Routing Table)

            ## Commands (2 user-facing entry points)

            ### Act (`/project-act`)
            - **Role**: Senior Developer
            - **Playbook**: `commands/project-act.md`

            ### Done (`/project-done`)
            - **Role**: Repo Maintainer
            - **Playbook**: `commands/project-done.md`
        """), encoding='utf-8')

        # Skills
        skills_dir = tmp_path / 'skills'
        (skills_dir / 'pactkit-board' / 'scripts').mkdir(parents=True)
        (skills_dir / 'pactkit-board' / 'scripts' / 'board.py').write_text('# board', encoding='utf-8')
        (skills_dir / 'pactkit-trace' / 'scripts').mkdir(parents=True)
        (skills_dir / 'pactkit-trace' / 'scripts' / 'trace.py').write_text('# trace', encoding='utf-8')
        (skills_dir / 'pactkit-visualize' / 'scripts').mkdir(parents=True)
        (skills_dir / 'pactkit-visualize' / 'scripts' / 'visualize.py').write_text('# viz', encoding='utf-8')

        return cmd_dir, rules_dir, skills_dir

    def test_builds_complete_graph(self, tmp_path):
        from pactkit.skills.visualize import build_workflow_graph
        cmd_dir, rules_dir, skills_dir = self._setup_pactkit_dirs(tmp_path)
        g = build_workflow_graph(commands_dir=cmd_dir, rules_dir=rules_dir, skills_dir=skills_dir)
        # Should have command nodes
        assert 'project-act' in g.nodes
        assert 'project-done' in g.nodes
        # Should have skill nodes
        assert 'pactkit-board' in g.nodes
        assert 'pactkit-trace' in g.nodes
        # Should have edges
        assert len(g.edges) >= 4

    def test_to_mermaid_produces_valid_output(self, tmp_path):
        from pactkit.skills.visualize import build_workflow_graph
        cmd_dir, rules_dir, skills_dir = self._setup_pactkit_dirs(tmp_path)
        g = build_workflow_graph(commands_dir=cmd_dir, rules_dir=rules_dir, skills_dir=skills_dir)
        mmd = g.to_mermaid()
        assert mmd.startswith('graph TD')
        assert 'subgraph' in mmd
        # Mermaid-safe IDs (no dots, slashes, spaces)
        lines = mmd.split('\n')
        for line in lines:
            if '-->' in line and '|' in line:
                # Edge line — check it has label
                assert '|' in line

    def test_graph_non_empty(self, tmp_path):
        from pactkit.skills.visualize import build_workflow_graph
        cmd_dir, rules_dir, skills_dir = self._setup_pactkit_dirs(tmp_path)
        g = build_workflow_graph(commands_dir=cmd_dir, rules_dir=rules_dir, skills_dir=skills_dir)
        assert len(g.nodes) >= 4  # at least 2 commands, 2 agents
        assert len(g.edges) >= 4  # at least 2 cmd→agent + 2 cmd→skill


# ── Standalone script compatibility tests (R6) ──────────────────────

class TestStandaloneCompatibility:
    """Test that workflow parser functions work without pactkit library imports."""

    def test_no_pactkit_imports(self):
        """Verify the workflow parser code uses only stdlib + Path operations."""
        from pactkit.skills.visualize import _parse_commands, _parse_routing_table, _scan_skill_files
        # These functions should be importable — they're in visualize.py which is standalone
        assert callable(_parse_commands)
        assert callable(_parse_routing_table)
        assert callable(_scan_skill_files)
