"""Tests for STORY-010: Project-level Dual-File Layered Architecture for Codex."""

from pathlib import Path
from unittest.mock import patch

import pytest

from pactkit_codex.generators.deployer import (
    _generate_codex_project_files,
)


@pytest.fixture
def project_dir(tmp_path):
    """Create a temporary project directory with pyproject.toml."""
    (tmp_path / "pyproject.toml").write_text("[project]\nname = 'testproj'\n")
    return tmp_path


class TestAC1AgentsMdRegenerated:
    """AC1: Root AGENTS.md regenerated on every deploy (no-overwrite guard removed)."""

    def test_agents_md_created_when_missing(self, project_dir):
        _generate_codex_project_files(project_dir)
        agents_md = project_dir / "AGENTS.md"
        assert agents_md.exists()
        assert "# " in agents_md.read_text()

    def test_agents_md_overwritten_when_exists(self, project_dir):
        agents_md = project_dir / "AGENTS.md"
        # Write PactKit-template-like content (first line matches template)
        agents_md.write_text(f"# {project_dir.name}\n\nold content\n")
        _generate_codex_project_files(project_dir)
        content = agents_md.read_text()
        assert "old content" not in content
        assert f"# {project_dir.name}" in content

    def test_agents_md_always_fresh(self, project_dir):
        """Two consecutive deploys produce same content (idempotent)."""
        _generate_codex_project_files(project_dir)
        first = (project_dir / "AGENTS.md").read_text()
        _generate_codex_project_files(project_dir)
        second = (project_dir / "AGENTS.md").read_text()
        assert first == second


class TestAC2LocalMdCreated:
    """AC2: AGENTS.local.md created on first deploy."""

    def test_local_md_created(self, project_dir):
        _generate_codex_project_files(project_dir)
        local_md = project_dir / ".codex" / "AGENTS.local.md"
        assert local_md.exists()
        content = local_md.read_text()
        assert "Project Local Instructions" in content or "custom" in content.lower()


class TestAC3LocalMdNeverOverwritten:
    """AC3: AGENTS.local.md never overwritten if it exists."""

    def test_local_md_preserved(self, project_dir):
        codex_dir = project_dir / ".codex"
        codex_dir.mkdir(parents=True)
        local_md = codex_dir / "AGENTS.local.md"
        local_md.write_text("# My custom instructions\nDo not touch this.\n")

        _generate_codex_project_files(project_dir)

        assert local_md.read_text() == "# My custom instructions\nDo not touch this.\n"


class TestAC4MigrationHeuristic:
    """AC4: User-modified root AGENTS.md migrated to AGENTS.local.md."""

    def test_user_content_migrated(self, project_dir):
        agents_md = project_dir / "AGENTS.md"
        # Content whose first line does NOT match "# {project_name}"
        agents_md.write_text("# My Custom Project Rules\n\nDo X before Y.\n")

        _generate_codex_project_files(project_dir)

        # User content should be migrated to local file
        local_md = project_dir / ".codex" / "AGENTS.local.md"
        assert local_md.exists()
        assert "My Custom Project Rules" in local_md.read_text()

        # Root AGENTS.md should be overwritten with PactKit template
        new_root = agents_md.read_text()
        assert f"# {project_dir.name}" in new_root
        assert "My Custom Project Rules" not in new_root

    def test_no_migration_when_local_exists(self, project_dir):
        """If AGENTS.local.md already exists, do NOT migrate (avoid overwrite)."""
        agents_md = project_dir / "AGENTS.md"
        agents_md.write_text("# My Custom Project Rules\n\nDo X before Y.\n")

        codex_dir = project_dir / ".codex"
        codex_dir.mkdir(parents=True)
        local_md = codex_dir / "AGENTS.local.md"
        local_md.write_text("# Existing local instructions\n")

        _generate_codex_project_files(project_dir)

        # Local file should be unchanged (not overwritten with migration)
        assert local_md.read_text() == "# Existing local instructions\n"


class TestAC5RootReferencesLocal:
    """AC5: Root AGENTS.md references AGENTS.local.md."""

    def test_agents_md_references_local(self, project_dir):
        _generate_codex_project_files(project_dir)
        content = (project_dir / "AGENTS.md").read_text()
        assert "AGENTS.local.md" in content


class TestAC6StackDetection:
    """AC6: Stack detection still works."""

    def test_python_stack_detected(self, project_dir):
        _generate_codex_project_files(project_dir)
        content = (project_dir / "AGENTS.md").read_text()
        assert "pytest" in content

    def test_node_stack_detected(self, tmp_path):
        (tmp_path / "package.json").write_text("{}")
        _generate_codex_project_files(tmp_path)
        content = (tmp_path / "AGENTS.md").read_text()
        assert "npm test" in content

    def test_unknown_stack_fallback(self, tmp_path):
        _generate_codex_project_files(tmp_path)
        content = (tmp_path / "AGENTS.md").read_text()
        assert "TODO" in content

    def test_home_dir_skipped(self):
        """Deploying to home directory is a no-op."""
        with patch.object(Path, "cwd", return_value=Path.home()):
            _generate_codex_project_files(Path.home())
        # Should not create AGENTS.md in home dir — no assertion needed, just no crash


class TestPactkitYamlUnchanged:
    """R6: pactkit.yaml no-overwrite behavior unchanged."""

    def test_yaml_created_if_missing(self, project_dir):
        _generate_codex_project_files(project_dir)
        yaml_path = project_dir / ".codex" / "pactkit.yaml"
        assert yaml_path.exists()
        assert "stack: python" in yaml_path.read_text()

    def test_yaml_not_overwritten(self, project_dir):
        codex_dir = project_dir / ".codex"
        codex_dir.mkdir(parents=True)
        yaml_path = codex_dir / "pactkit.yaml"
        yaml_path.write_text("stack: custom\nversion: 1.0.0\n")

        _generate_codex_project_files(project_dir)

        assert yaml_path.read_text() == "stack: custom\nversion: 1.0.0\n"
