import sys
from pathlib import Path

# Add scaffold script to path (use source copy in project)
SCAFFOLD_SCRIPT = Path(__file__).resolve().parent.parent.parent / 'src' / 'pactkit' / 'skills' / 'scaffold.py'
sys.path.insert(0, str(SCAFFOLD_SCRIPT.parent))

# We'll import after the function exists
# For now, define what we expect to test


class TestCreateSkillValidation:
    """Scenario 3: skill_name format validation."""

    def test_rejects_uppercase(self, tmp_path):
        from scaffold import create_skill
        result = create_skill('My_Tool', 'desc', base_dir=str(tmp_path))
        assert '❌' in result
        assert 'Invalid skill name' in result
        assert not (tmp_path / 'My_Tool').exists()

    def test_rejects_underscore(self, tmp_path):
        from scaffold import create_skill
        result = create_skill('my_tool', 'desc', base_dir=str(tmp_path))
        assert '❌' in result
        assert 'Invalid skill name' in result

    def test_rejects_spaces(self, tmp_path):
        from scaffold import create_skill
        result = create_skill('my tool', 'desc', base_dir=str(tmp_path))
        assert '❌' in result
        assert 'Invalid skill name' in result

    def test_accepts_valid_name(self, tmp_path):
        from scaffold import create_skill
        result = create_skill('my-tool', 'A tool', base_dir=str(tmp_path))
        assert '✅' in result

    def test_accepts_numbers_and_hyphens(self, tmp_path):
        from scaffold import create_skill
        result = create_skill('tool-v2', 'desc', base_dir=str(tmp_path))
        assert '✅' in result

    def test_rejects_leading_hyphen(self, tmp_path):
        from scaffold import create_skill
        result = create_skill('-tool', 'desc', base_dir=str(tmp_path))
        assert '❌' in result
        assert 'Invalid skill name' in result

    def test_rejects_pure_hyphens(self, tmp_path):
        from scaffold import create_skill
        result = create_skill('---', 'desc', base_dir=str(tmp_path))
        assert '❌' in result
        assert 'Invalid skill name' in result

    def test_rejects_trailing_hyphen(self, tmp_path):
        from scaffold import create_skill
        result = create_skill('tool-', 'desc', base_dir=str(tmp_path))
        assert '❌' in result
        assert 'Invalid skill name' in result

    def test_rejects_pure_digits(self, tmp_path):
        from scaffold import create_skill
        result = create_skill('123', 'desc', base_dir=str(tmp_path))
        assert '❌' in result
        assert 'Invalid skill name' in result


class TestCreateSkillSuccess:
    """Scenario 1: successful skill creation."""

    def test_creates_skill_directory(self, tmp_path):
        from scaffold import create_skill
        create_skill('my-tool', 'A tool for something', base_dir=str(tmp_path))
        assert (tmp_path / 'my-tool').is_dir()

    def test_creates_skill_md(self, tmp_path):
        from scaffold import create_skill
        create_skill('my-tool', 'A tool for something', base_dir=str(tmp_path))
        skill_md = tmp_path / 'my-tool' / 'SKILL.md'
        assert skill_md.exists()
        content = skill_md.read_text()
        # YAML frontmatter
        assert 'name: my-tool' in content
        assert 'A tool for something' in content
        # Required sections
        assert '## Prerequisites' in content
        assert '## Command Reference' in content
        assert '## Usage Scenarios' in content

    def test_skill_md_uses_absolute_path(self, tmp_path):
        """BUG-001 follow-up: generated SKILL.md must use absolute script path (base_dir-derived)."""
        from scaffold import create_skill
        create_skill('my-tool', 'A tool', base_dir=str(tmp_path))
        content = (tmp_path / 'my-tool' / 'SKILL.md').read_text()
        # STORY-slim-027 R8: path derived from base_dir, not hardcoded ~/.claude/skills
        assert str(tmp_path / 'my-tool' / 'scripts' / 'my_tool.py') in content
        assert 'python3 scripts/' not in content

    def test_creates_script_file(self, tmp_path):
        from scaffold import create_skill
        create_skill('my-tool', 'A tool', base_dir=str(tmp_path))
        script = tmp_path / 'my-tool' / 'scripts' / 'my_tool.py'
        assert script.exists()
        content = script.read_text()
        assert 'argparse' in content
        assert "if __name__ == '__main__'" in content

    def test_creates_references_gitkeep(self, tmp_path):
        from scaffold import create_skill
        create_skill('my-tool', 'A tool', base_dir=str(tmp_path))
        gitkeep = tmp_path / 'my-tool' / 'references' / '.gitkeep'
        assert gitkeep.exists()

    def test_output_message(self, tmp_path):
        from scaffold import create_skill
        result = create_skill('my-tool', 'A tool', base_dir=str(tmp_path))
        assert '✅' in result
        assert 'my-tool' in result

    def test_clean_name_conversion(self, tmp_path):
        """Hyphens in skill name become underscores in script filename."""
        from scaffold import create_skill
        create_skill('my-cool-tool', 'desc', base_dir=str(tmp_path))
        script = tmp_path / 'my-cool-tool' / 'scripts' / 'my_cool_tool.py'
        assert script.exists()

    def test_description_with_double_quotes(self, tmp_path):
        """Double quotes in description are escaped in YAML frontmatter."""
        from scaffold import create_skill
        result = create_skill('my-tool', 'A "great" tool', base_dir=str(tmp_path))
        assert '✅' in result
        content = (tmp_path / 'my-tool' / 'SKILL.md').read_text()
        assert r'description: "A \"great\" tool"' in content


class TestCreateSkillAlreadyExists:
    """Scenario 2: skill already exists."""

    def test_rejects_existing_skill(self, tmp_path):
        from scaffold import create_skill
        # Create skill first time
        create_skill('my-tool', 'first', base_dir=str(tmp_path))
        # Second attempt should fail
        result = create_skill('my-tool', 'second', base_dir=str(tmp_path))
        assert '❌' in result
        assert 'already exists' in result
        # Original SKILL.md should be unchanged
        content = (tmp_path / 'my-tool' / 'SKILL.md').read_text()
        assert 'first' in content
