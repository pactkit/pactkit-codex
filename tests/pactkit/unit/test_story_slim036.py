"""Tests for STORY-slim-036: visualize --mode workflow."""
import textwrap


def _setup_pactkit_tree(tmp_path):
    """Create a minimal PactKit directory for workflow visualize tests."""
    cmd_dir = tmp_path / '.claude' / 'commands'
    cmd_dir.mkdir(parents=True)
    (cmd_dir / 'project-act.md').write_text(textwrap.dedent("""\
        # Command: Act
        - **Agent**: Senior Developer
        Use pactkit-trace skill.
    """), encoding='utf-8')

    rules_dir = tmp_path / '.claude' / 'rules'
    rules_dir.mkdir(parents=True)
    (rules_dir / '04-routing-table.md').write_text(textwrap.dedent("""\
        # Command Reference (Routing Table)
        ## Commands (1 user-facing entry points)
        ### Act (`/project-act`)
        - **Role**: Senior Developer
        - **Playbook**: `commands/project-act.md`
    """), encoding='utf-8')

    skills_dir = tmp_path / '.claude' / 'skills'
    (skills_dir / 'pactkit-trace' / 'scripts').mkdir(parents=True)
    (skills_dir / 'pactkit-trace' / 'scripts' / 'trace.py').write_text('# trace', encoding='utf-8')

    # Need pyproject.toml for stack detection
    (tmp_path / 'pyproject.toml').write_text('[project]\nname = "test"', encoding='utf-8')

    return tmp_path


class TestVisualizeWorkflowMode:
    """Test --mode workflow integration in visualize()."""

    def test_workflow_mode_creates_mmd(self, tmp_path):
        from pactkit.skills.visualize import visualize
        root = _setup_pactkit_tree(tmp_path)
        result = visualize(target=str(root), mode='workflow')
        assert 'workflow_graph.mmd' in result
        mmd_path = root / 'docs' / 'architecture' / 'graphs' / 'workflow_graph.mmd'
        assert mmd_path.exists()

    def test_workflow_mmd_contains_graph_td(self, tmp_path):
        from pactkit.skills.visualize import visualize
        root = _setup_pactkit_tree(tmp_path)
        visualize(target=str(root), mode='workflow')
        mmd_path = root / 'docs' / 'architecture' / 'graphs' / 'workflow_graph.mmd'
        content = mmd_path.read_text(encoding='utf-8')
        assert content.startswith('graph TD')

    def test_workflow_mmd_has_subgraphs(self, tmp_path):
        from pactkit.skills.visualize import visualize
        root = _setup_pactkit_tree(tmp_path)
        visualize(target=str(root), mode='workflow')
        mmd_path = root / 'docs' / 'architecture' / 'graphs' / 'workflow_graph.mmd'
        content = mmd_path.read_text(encoding='utf-8')
        assert 'subgraph Commands' in content
        assert 'subgraph Skills' in content

    def test_workflow_mmd_has_edge_labels(self, tmp_path):
        from pactkit.skills.visualize import visualize
        root = _setup_pactkit_tree(tmp_path)
        visualize(target=str(root), mode='workflow')
        mmd_path = root / 'docs' / 'architecture' / 'graphs' / 'workflow_graph.mmd'
        content = mmd_path.read_text(encoding='utf-8')
        assert '|invokes|' in content or '|depends_on|' in content

    def test_existing_modes_unaffected(self, tmp_path):
        """Ensure mode='file' still works as before."""
        from pactkit.skills.visualize import visualize
        root = _setup_pactkit_tree(tmp_path)
        # Create a minimal Python file for file mode
        src_dir = root / 'src'
        src_dir.mkdir()
        (src_dir / 'main.py').write_text('import os\n', encoding='utf-8')
        result = visualize(target=str(root), mode='file')
        assert 'code_graph.mmd' in result

    def test_default_mode_is_file(self, tmp_path):
        from pactkit.skills.visualize import visualize
        root = _setup_pactkit_tree(tmp_path)
        src_dir = root / 'src'
        src_dir.mkdir()
        (src_dir / 'main.py').write_text('x = 1\n', encoding='utf-8')
        result = visualize(target=str(root))
        assert 'code_graph.mmd' in result


class TestWorkflowLazy:
    """Test lazy generation for workflow mode."""

    def test_lazy_regenerates_when_missing(self, tmp_path):
        from pactkit.skills.visualize import visualize
        root = _setup_pactkit_tree(tmp_path)
        result = visualize(target=str(root), mode='workflow', lazy=True)
        assert 'workflow_graph.mmd' in result

    def test_lazy_skips_when_up_to_date(self, tmp_path):
        from pactkit.skills.visualize import visualize
        root = _setup_pactkit_tree(tmp_path)
        # First generation
        visualize(target=str(root), mode='workflow', lazy=True)
        # Second call — should skip
        result = visualize(target=str(root), mode='workflow', lazy=True)
        assert 'up-to-date' in result.lower() or 'skip' in result.lower()
