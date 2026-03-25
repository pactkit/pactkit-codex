"""Tests for STORY-003: Project-level AGENTS.md and pactkit.yaml Generator."""


import pytest
import yaml


@pytest.fixture
def project_root(tmp_path):
    """Temporary project root directory."""
    return tmp_path / "my-project"


class TestProjectLevelFiles:
    """AC1-AC6: Project-level AGENTS.md + pactkit.yaml generation for Codex."""

    def _generate(self, project_root, pre_create_agents_md=False, pre_create_yaml=False):
        """Helper to generate project files."""
        from pactkit_codex.generators.deployer import _generate_codex_project_files

        project_root.mkdir(parents=True, exist_ok=True)
        if pre_create_agents_md:
            (project_root / "AGENTS.md").write_text("# User's existing file\n")
        if pre_create_yaml:
            codex_dir = project_root / ".codex"
            codex_dir.mkdir(parents=True, exist_ok=True)
            (codex_dir / "pactkit.yaml").write_text("stack: node\nversion: 1.0.0\n")
        return _generate_codex_project_files(project_root)

    def test_ac1_fresh_project(self, project_root):
        """AC1: Fresh project gets both AGENTS.md and .codex/pactkit.yaml."""
        self._generate(project_root)
        assert (project_root / "AGENTS.md").exists()
        assert (project_root / ".codex" / "pactkit.yaml").exists()

    def test_ac2_agents_md_always_regenerated(self, project_root):
        """AC2: AGENTS.md is always regenerated (STORY-010 dual-file architecture).

        User content is migrated to .codex/AGENTS.local.md if detected.
        """
        self._generate(project_root, pre_create_agents_md=True)
        content = (project_root / "AGENTS.md").read_text()
        # STORY-010: Root AGENTS.md is PactKit-managed, always regenerated
        assert "my-project" in content
        # User content migrated to local file
        local_md = project_root / ".codex" / "AGENTS.local.md"
        assert local_md.exists()
        assert "User's existing file" in local_md.read_text()

    def test_ac3_no_overwrite_yaml(self, project_root, capsys):
        """AC3: Existing pactkit.yaml is NOT overwritten."""
        self._generate(project_root, pre_create_yaml=True)
        content = (project_root / ".codex" / "pactkit.yaml").read_text()
        assert "node" in content  # Original content preserved
        assert "1.0.0" in content

    def test_ac4_yaml_fields(self, project_root):
        """AC4: pactkit.yaml contains required fields."""
        self._generate(project_root)
        yaml_path = project_root / ".codex" / "pactkit.yaml"
        data = yaml.safe_load(yaml_path.read_text())
        assert "stack" in data
        assert data["stack"]  # non-empty
        assert data["version"] == "0.0.1"
        assert data["root"] == "."
        assert "developer" in data

    def test_ac5_agents_md_content(self, project_root):
        """AC5: AGENTS.md contains project name, dev commands, and context ref."""
        self._generate(project_root)
        content = (project_root / "AGENTS.md").read_text()
        assert "my-project" in content  # project name
        assert "## Dev Commands" in content
        assert "context.md" in content  # reference to context.md

    def test_ac6_python_stack_detection(self, project_root):
        """AC6: Python project detected from pyproject.toml."""
        project_root.mkdir(parents=True, exist_ok=True)
        (project_root / "pyproject.toml").write_text("[build-system]\n")
        self._generate(project_root)
        yaml_path = project_root / ".codex" / "pactkit.yaml"
        data = yaml.safe_load(yaml_path.read_text())
        assert data["stack"] == "python"
        content = (project_root / "AGENTS.md").read_text()
        assert "pytest" in content

    def test_node_stack_detection(self, project_root):
        """Stack detection: Node project from package.json."""
        project_root.mkdir(parents=True, exist_ok=True)
        (project_root / "package.json").write_text("{}\n")
        self._generate(project_root)
        yaml_path = project_root / ".codex" / "pactkit.yaml"
        data = yaml.safe_load(yaml_path.read_text())
        assert data["stack"] == "node"
        content = (project_root / "AGENTS.md").read_text()
        assert "npm test" in content

    def test_unknown_stack(self, project_root):
        """Stack detection: Unknown stack defaults gracefully."""
        self._generate(project_root)
        yaml_path = project_root / ".codex" / "pactkit.yaml"
        data = yaml.safe_load(yaml_path.read_text())
        assert data["stack"] == "unknown"
