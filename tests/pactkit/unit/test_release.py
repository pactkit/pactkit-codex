"""Tests for STORY-011: Upgrade project-release to v20.0."""
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


def _exec_board():
    """Load BOARD_SOURCE into exec globals and return the namespace."""
    from pactkit.prompts import BOARD_SOURCE
    g = {}
    exec(BOARD_SOURCE, g)
    return g


# ==============================================================================
# Scenario 1: snapshot saves three graph files
# ==============================================================================
class TestSnapshotSavesGraphs:
    def test_snapshot_copies_existing_graphs(self, tmp_path):
        graphs = tmp_path / 'docs/architecture/graphs'
        graphs.mkdir(parents=True)
        (graphs / 'code_graph.mmd').write_text('graph TD', encoding='utf-8')
        (graphs / 'class_graph.mmd').write_text('classDiagram', encoding='utf-8')
        (graphs / 'call_graph.mmd').write_text('graph TD', encoding='utf-8')

        import os
        old_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            g = _exec_board()
            result = g['snapshot_graph']('v1.0.0')
            snap_dir = tmp_path / 'docs/architecture/snapshots'
            assert (snap_dir / 'v1.0.0_code_graph.mmd').exists()
            assert (snap_dir / 'v1.0.0_class_graph.mmd').exists()
            assert (snap_dir / 'v1.0.0_call_graph.mmd').exists()
            assert '3' in result
        finally:
            os.chdir(old_cwd)

    def test_snapshot_skips_missing_graphs(self, tmp_path):
        graphs = tmp_path / 'docs/architecture/graphs'
        graphs.mkdir(parents=True)
        (graphs / 'code_graph.mmd').write_text('graph TD', encoding='utf-8')

        import os
        old_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            g = _exec_board()
            result = g['snapshot_graph']('v2.0.0')
            snap_dir = tmp_path / 'docs/architecture/snapshots'
            assert (snap_dir / 'v2.0.0_code_graph.mmd').exists()
            assert not (snap_dir / 'v2.0.0_class_graph.mmd').exists()
            assert '1' in result
        finally:
            os.chdir(old_cwd)


# ==============================================================================
# Scenario 2: snapshot creates directory automatically
# ==============================================================================
class TestSnapshotAutoCreateDir:
    def test_snapshots_dir_created(self, tmp_path):
        graphs = tmp_path / 'docs/architecture/graphs'
        graphs.mkdir(parents=True)
        (graphs / 'code_graph.mmd').write_text('graph TD', encoding='utf-8')

        import os
        old_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            snap_dir = tmp_path / 'docs/architecture/snapshots'
            assert not snap_dir.exists()
            g = _exec_board()
            g['snapshot_graph']('v1.0.0')
            assert snap_dir.exists()
        finally:
            os.chdir(old_cwd)


# ==============================================================================
# Scenario 3: release command has correct paths
# ==============================================================================
class TestReleaseSkillContent:
    """Release is now a skill (STORY-011), check SKILL_RELEASE_MD."""

    def test_no_pactkit_tools_reference(self):
        from pactkit.prompts import SKILL_RELEASE_MD
        assert 'pactkit_tools' not in SKILL_RELEASE_MD

    def test_has_visualize_reference(self):
        from pactkit.prompts import SKILL_RELEASE_MD
        assert 'visualize' in SKILL_RELEASE_MD.lower() or 'snapshot' in SKILL_RELEASE_MD.lower()

    def test_has_board_reference(self):
        from pactkit.prompts import SKILL_RELEASE_MD
        assert 'board' in SKILL_RELEASE_MD.lower() or 'archive' in SKILL_RELEASE_MD.lower()


# ==============================================================================
# Scenario 4: release command in COMMANDS_CONTENT
# ==============================================================================
class TestReleaseIsSkill:
    """Release is now a skill (STORY-011), not a command."""

    def test_release_skill_exists(self):
        from pactkit.prompts import SKILL_RELEASE_MD
        assert isinstance(SKILL_RELEASE_MD, str)
        assert len(SKILL_RELEASE_MD) > 50


# ==============================================================================
# Scenario 5: update_version writes to pactkit.yaml
# ==============================================================================
class TestUpdateVersion:
    def test_update_version_writes_yaml(self, tmp_path):
        claude_dir = tmp_path / '.claude'
        claude_dir.mkdir()
        yaml_file = claude_dir / 'pactkit.yaml'
        yaml_file.write_text('stack: python\nversion: 0.0.1\nroot: .\n', encoding='utf-8')

        import os
        old_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            g = _exec_board()
            result = g['update_version']('v1.0.0')
            content = yaml_file.read_text()
            assert 'v1.0.0' in content
            assert '0.0.1' not in content
        finally:
            os.chdir(old_cwd)

    def test_update_version_no_yaml_graceful(self, tmp_path):
        import os
        old_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            g = _exec_board()
            result = g['update_version']('v1.0.0')
            assert '⚠' in result or 'skip' in result.lower() or 'No' in result
        finally:
            os.chdir(old_cwd)


# ==============================================================================
# Scenario 6: frontmatter compliance
# ==============================================================================
class TestReleaseSkillFrontmatter:
    """SKILL_RELEASE_MD has proper frontmatter."""

    def test_has_frontmatter(self):
        from pactkit.prompts import SKILL_RELEASE_MD
        assert SKILL_RELEASE_MD.strip().startswith('---')

    def test_has_description(self):
        from pactkit.prompts import SKILL_RELEASE_MD
        assert 'description:' in SKILL_RELEASE_MD
