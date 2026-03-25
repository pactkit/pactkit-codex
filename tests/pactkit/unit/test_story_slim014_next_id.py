"""Tests for pactkit next-id (STORY-slim-014 R1)."""
from pactkit.id_generator import next_story_id


class TestNextStoryId:
    """Scenario 2 from spec: pactkit next-id replaces manual ID generation."""

    def test_next_id_with_existing_stories(self, tmp_path):
        """Given STORY-slim-013.md exists, return STORY-slim-014."""
        specs = tmp_path / "docs" / "specs"
        specs.mkdir(parents=True)
        (specs / "STORY-slim-010.md").write_text("# S10")
        (specs / "STORY-slim-013.md").write_text("# S13")
        (specs / "STORY-slim-007.md").write_text("# S7")

        result = next_story_id(specs_dir=specs, developer="slim")
        assert result == "STORY-slim-014"

    def test_next_id_no_existing_stories(self, tmp_path):
        """Given no stories exist, return STORY-slim-001."""
        specs = tmp_path / "docs" / "specs"
        specs.mkdir(parents=True)

        result = next_story_id(specs_dir=specs, developer="slim")
        assert result == "STORY-slim-001"

    def test_next_id_no_developer(self, tmp_path):
        """Given developer is empty, return STORY-001 format."""
        specs = tmp_path / "docs" / "specs"
        specs.mkdir(parents=True)

        result = next_story_id(specs_dir=specs, developer="")
        assert result == "STORY-001"

    def test_next_id_no_developer_with_existing(self, tmp_path):
        """Given developer empty and STORY-005.md exists, return STORY-006."""
        specs = tmp_path / "docs" / "specs"
        specs.mkdir(parents=True)
        (specs / "STORY-005.md").write_text("# S5")
        (specs / "STORY-003.md").write_text("# S3")

        result = next_story_id(specs_dir=specs, developer="")
        assert result == "STORY-006"

    def test_next_id_ignores_other_prefixes(self, tmp_path):
        """Given HOTFIX and BUG specs exist, only count STORY prefix."""
        specs = tmp_path / "docs" / "specs"
        specs.mkdir(parents=True)
        (specs / "STORY-slim-002.md").write_text("# S")
        (specs / "HOTFIX-slim-010.md").write_text("# H")
        (specs / "BUG-slim-020.md").write_text("# B")

        result = next_story_id(specs_dir=specs, developer="slim")
        assert result == "STORY-slim-003"

    def test_next_id_ignores_other_developers(self, tmp_path):
        """Given stories from other developers, only count own stories."""
        specs = tmp_path / "docs" / "specs"
        specs.mkdir(parents=True)
        (specs / "STORY-slim-005.md").write_text("# S")
        (specs / "STORY-bob-020.md").write_text("# S")

        result = next_story_id(specs_dir=specs, developer="slim")
        assert result == "STORY-slim-006"

    def test_next_id_specs_dir_missing(self, tmp_path):
        """Given specs dir doesn't exist, return first ID."""
        specs = tmp_path / "docs" / "specs"
        # Don't create the directory

        result = next_story_id(specs_dir=specs, developer="slim")
        assert result == "STORY-slim-001"

    def test_next_id_three_digit_padding(self, tmp_path):
        """IDs should be zero-padded to 3 digits."""
        specs = tmp_path / "docs" / "specs"
        specs.mkdir(parents=True)

        result = next_story_id(specs_dir=specs, developer="slim")
        assert result == "STORY-slim-001"
        # Verify zero-padding
        assert result.endswith("001")
