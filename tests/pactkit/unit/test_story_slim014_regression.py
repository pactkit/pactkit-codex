"""Tests for pactkit regression (STORY-slim-014 R1).

Scenario 3 from spec: pactkit regression replaces decision tree prompt.
"""
from pactkit.regression import classify_changes


class TestClassifyChangesDocOnly:
    """Doc-only changes should be skipped."""

    def test_docs_only(self):
        """All files under docs/ → skip."""
        files = ["docs/specs/STORY-slim-014.md", "docs/product/context.md"]
        strategy, reason = classify_changes(files)
        assert strategy == "skip"
        assert "doc" in reason.lower()

    def test_markdown_files_only(self):
        """All .md files at root → skip."""
        files = ["README.md", "CHANGELOG.md"]
        strategy, reason = classify_changes(files)
        assert strategy == "skip"
        assert "doc" in reason.lower()

    def test_readme_file(self):
        """README file → skip."""
        files = ["README.md"]
        strategy, reason = classify_changes(files)
        assert strategy == "skip"

    def test_txt_files_only(self):
        """All .txt files → skip."""
        files = ["notes.txt", "docs/design.txt"]
        strategy, reason = classify_changes(files)
        assert strategy == "skip"
        assert "doc" in reason.lower()

    def test_test_files_only(self):
        """Only test files changed → skip (tests/** matches doc-only pattern)."""
        files = ["tests/unit/test_foo.py", "tests/e2e/test_bar.py"]
        strategy, reason = classify_changes(files)
        assert strategy == "skip"
        assert "doc" in reason.lower()

    def test_empty_list(self):
        """Empty file list → skip (nothing changed)."""
        strategy, reason = classify_changes([])
        assert strategy == "skip"


class TestClassifyChangesVersionBump:
    """Version/dependency file changes trigger full regression."""

    def test_pyproject_toml(self):
        """pyproject.toml changed → full."""
        files = ["pyproject.toml"]
        strategy, reason = classify_changes(files)
        assert strategy == "full"
        assert "version" in reason.lower() or "depend" in reason.lower()

    def test_package_json(self):
        """package.json changed → full."""
        files = ["package.json"]
        strategy, reason = classify_changes(files)
        assert strategy == "full"
        assert "version" in reason.lower() or "depend" in reason.lower()

    def test_cargo_toml(self):
        """Cargo.toml changed → full."""
        files = ["Cargo.toml"]
        strategy, reason = classify_changes(files)
        assert strategy == "full"
        assert "version" in reason.lower() or "depend" in reason.lower()

    def test_go_mod(self):
        """go.mod changed → full."""
        files = ["go.mod"]
        strategy, reason = classify_changes(files)
        assert strategy == "full"
        assert "version" in reason.lower() or "depend" in reason.lower()

    def test_version_file_mixed_with_docs(self):
        """pyproject.toml + docs → full (version bump takes priority over doc-only)."""
        files = ["pyproject.toml", "README.md", "docs/specs/STORY.md"]
        strategy, reason = classify_changes(files)
        assert strategy == "full"


class TestClassifyChangesImpact:
    """Source file changes → impact (run mapped tests)."""

    def test_single_source_file(self):
        """A .py source file changed → impact."""
        files = ["src/pactkit/cli.py"]
        strategy, reason = classify_changes(files)
        assert strategy == "impact"

    def test_mixed_docs_and_source(self):
        """Docs + source file mixed → impact (not doc-only)."""
        files = ["docs/specs/STORY.md", "src/pactkit/regression.py"]
        strategy, reason = classify_changes(files)
        assert strategy == "impact"

    def test_js_source_file(self):
        """A .js file changed → impact."""
        files = ["src/app.js"]
        strategy, reason = classify_changes(files)
        assert strategy == "impact"

    def test_config_file(self):
        """A config .yaml file (not a package manifest) → impact."""
        files = ["config.yaml"]
        strategy, reason = classify_changes(files)
        assert strategy == "impact"

    def test_source_alongside_version_file(self):
        """Source file + package.json → full (version takes priority)."""
        files = ["src/app.py", "package.json"]
        strategy, reason = classify_changes(files)
        assert strategy == "full"
