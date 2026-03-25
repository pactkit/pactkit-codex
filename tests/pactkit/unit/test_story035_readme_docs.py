"""
STORY-035: Update README and docs directory documentation.

Tests verify that README.md and CHANGELOG.md have complete, accurate content.
"""
from pathlib import Path

README = Path(__file__).resolve().parents[2] / "README.md"
CHANGELOG = Path(__file__).resolve().parents[2] / "CHANGELOG.md"


def _readme():
    return README.read_text(encoding="utf-8")


def _changelog():
    return CHANGELOG.read_text(encoding="utf-8")


# ===========================================================================
# AC1: docs/ directory documented in README
# ===========================================================================
class TestAC1DocsDirectoryDocumented:
    """README must document the docs/ directory structure."""

    def test_readme_has_project_structure_section(self):
        content = _readme()
        lower = content.lower()
        assert "project structure" in lower or "docs/" in lower

    def test_readme_documents_specs_dir(self):
        content = _readme()
        assert "docs/specs" in content or "specs/" in content

    def test_readme_documents_sprint_board(self):
        content = _readme()
        assert "sprint_board" in content

    def test_readme_documents_context_md(self):
        content = _readme()
        assert "context.md" in content

    def test_readme_documents_lessons_md(self):
        content = _readme()
        assert "lessons.md" in content

    def test_readme_documents_architecture_graphs(self):
        content = _readme()
        lower = content.lower()
        assert "architecture" in lower and "graph" in lower


# ===========================================================================
# AC2: pactkit.yaml configuration reference
# ===========================================================================
class TestAC2ConfigReference:
    """README must document pactkit.yaml fields."""

    def test_readme_has_config_fields_section(self):
        """Should have a configuration reference section."""
        content = _readme()
        lower = content.lower()
        assert "pactkit.yaml" in lower and ("field" in lower or "config" in lower)

    def test_readme_documents_ci_config(self):
        content = _readme()
        lower = content.lower()
        assert "ci" in lower and "provider" in lower

    def test_readme_documents_hooks_config(self):
        content = _readme()
        assert "hooks" in content.lower()

    def test_readme_documents_lint_blocking(self):
        content = _readme()
        assert "lint_blocking" in content

    def test_readme_documents_auto_fix(self):
        content = _readme()
        assert "auto_fix" in content

    def test_readme_documents_issue_tracker(self):
        content = _readme()
        assert "issue_tracker" in content

    def test_readme_documents_exclude(self):
        content = _readme()
        assert "exclude" in content


# ===========================================================================
# AC3: CHANGELOG complete for v1.3.0
# ===========================================================================
class TestAC3ChangelogComplete:
    """CHANGELOG must have entries for all v1.3.0 stories and bugs."""

    def test_changelog_has_story_031(self):
        assert "STORY-031" in _changelog()

    def test_changelog_has_story_032(self):
        assert "STORY-032" in _changelog()

    def test_changelog_has_story_033(self):
        assert "STORY-033" in _changelog()

    def test_changelog_has_story_034(self):
        assert "STORY-034" in _changelog()

    def test_changelog_has_bug_006(self):
        assert "BUG-006" in _changelog()

    def test_changelog_has_bug_007(self):
        assert "BUG-007" in _changelog()

    def test_changelog_has_bug_008(self):
        assert "BUG-008" in _changelog()

    def test_changelog_has_bug_009(self):
        assert "BUG-009" in _changelog()


# ===========================================================================
# AC4: Skills section complete — all 9 skills listed
# ===========================================================================
class TestAC4SkillsSectionComplete:
    """README Skills section must list all 9 skills."""

    def test_readme_lists_pactkit_board(self):
        assert "pactkit-board" in _readme()

    def test_readme_lists_pactkit_visualize(self):
        assert "pactkit-visualize" in _readme()

    def test_readme_lists_pactkit_scaffold(self):
        assert "pactkit-scaffold" in _readme()

    def test_readme_lists_pactkit_doctor(self):
        assert "pactkit-doctor" in _readme()

    def test_readme_lists_pactkit_draw(self):
        assert "pactkit-draw" in _readme()

    def test_readme_lists_pactkit_release(self):
        assert "pactkit-release" in _readme()

    def test_readme_lists_pactkit_review(self):
        assert "pactkit-review" in _readme()

    def test_readme_lists_pactkit_status(self):
        assert "pactkit-status" in _readme()

    def test_readme_lists_pactkit_trace(self):
        assert "pactkit-trace" in _readme()
