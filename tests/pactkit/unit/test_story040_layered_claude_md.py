"""
STORY-040: Project CLAUDE.md Layered Architecture — Separate Framework and User Content

Tests for the dual-file architecture:
- CLAUDE.md: PactKit-managed (regenerated on every update)
- CLAUDE.local.md: User-owned (never touched after creation)
"""
from unittest.mock import patch


def _deployer():
    from pactkit.generators import deployer
    return deployer


# ===========================================================================
# Scenario 1: Fresh project (no CLAUDE.md exists)
# ===========================================================================

class TestScenario1FreshProject:
    """Fresh project with no existing CLAUDE.md or CLAUDE.local.md."""

    def test_fresh_project_creates_claude_md(self, tmp_path):
        """Given no files exist, CLAUDE.md is created with framework content."""
        project_root = tmp_path / 'myproject'
        project_root.mkdir()
        claude_dir = project_root / '.claude'
        claude_dir.mkdir()

        config = {'venv': {'auto_detect': False}, 'stack': 'python'}

        with patch('pactkit.generators.deployer.Path.cwd', return_value=project_root):
            _deployer()._generate_project_claude_md(config)

        claude_md = claude_dir / 'CLAUDE.md'
        assert claude_md.exists()
        content = claude_md.read_text()
        # Framework content
        assert '# myproject' in content
        assert 'Dev Commands' in content

    def test_fresh_project_creates_claude_local_md(self, tmp_path):
        """Given no files exist, CLAUDE.local.md is created with template."""
        project_root = tmp_path / 'myproject'
        project_root.mkdir()
        claude_dir = project_root / '.claude'
        claude_dir.mkdir()

        config = {'venv': {'auto_detect': False}, 'stack': 'python'}

        with patch('pactkit.generators.deployer.Path.cwd', return_value=project_root):
            _deployer()._generate_project_claude_md(config)

        claude_local = claude_dir / 'CLAUDE.local.md'
        assert claude_local.exists()
        content = claude_local.read_text()
        # Template header
        assert 'Project Local Instructions' in content
        assert 'PactKit manages a venv block at the top' in content

    def test_fresh_project_claude_md_imports_claude_local_md(self, tmp_path):
        """CLAUDE.md must import CLAUDE.local.md via @ reference."""
        project_root = tmp_path / 'myproject'
        project_root.mkdir()
        claude_dir = project_root / '.claude'
        claude_dir.mkdir()

        config = {'venv': {'auto_detect': False}, 'stack': 'python'}

        with patch('pactkit.generators.deployer.Path.cwd', return_value=project_root):
            _deployer()._generate_project_claude_md(config)

        content = (claude_dir / 'CLAUDE.md').read_text()
        # R2: Import CLAUDE.local.md
        assert '@./.claude/CLAUDE.local.md' in content
        # Order check: context.md before CLAUDE.local.md
        lines = content.split('\n')
        context_idx = next((i for i, l in enumerate(lines) if '@./docs/product/context.md' in l), -1)
        local_idx = next((i for i, l in enumerate(lines) if '@./.claude/CLAUDE.local.md' in l), -1)
        assert context_idx < local_idx, "context.md should come before CLAUDE.local.md"


# ===========================================================================
# Scenario 2: Subsequent update (both files exist)
# ===========================================================================

class TestScenario2SubsequentUpdate:
    """Subsequent update where both CLAUDE.md and CLAUDE.local.md exist."""

    def test_claude_md_is_regenerated(self, tmp_path):
        """Given both files exist, CLAUDE.md is regenerated with latest template."""
        project_root = tmp_path / 'myproject'
        project_root.mkdir()
        claude_dir = project_root / '.claude'
        claude_dir.mkdir()

        # Create existing CLAUDE.md with old content
        claude_md = claude_dir / 'CLAUDE.md'
        claude_md.write_text("# Old PactKit template\nOld content")

        # Create existing CLAUDE.local.md
        claude_local = claude_dir / 'CLAUDE.local.md'
        user_content = "# My custom instructions\nDo NOT lose this!"
        claude_local.write_text(user_content)

        config = {'venv': {'auto_detect': False}, 'stack': 'python'}

        with patch('pactkit.generators.deployer.Path.cwd', return_value=project_root):
            _deployer()._generate_project_claude_md(config)

        # CLAUDE.md should be regenerated (not the old content)
        new_content = claude_md.read_text()
        assert 'Old content' not in new_content
        assert '# myproject' in new_content
        assert '@./.claude/CLAUDE.local.md' in new_content

    def test_claude_local_md_not_modified(self, tmp_path):
        """Given both files exist, CLAUDE.local.md is NOT modified."""
        project_root = tmp_path / 'myproject'
        project_root.mkdir()
        claude_dir = project_root / '.claude'
        claude_dir.mkdir()

        # Create existing files
        (claude_dir / 'CLAUDE.md').write_text("# Old")
        user_content = "# My custom instructions\nDo NOT lose this!"
        claude_local = claude_dir / 'CLAUDE.local.md'
        claude_local.write_text(user_content)

        config = {'venv': {'auto_detect': False}, 'stack': 'python'}

        with patch('pactkit.generators.deployer.Path.cwd', return_value=project_root):
            _deployer()._generate_project_claude_md(config)

        # CLAUDE.local.md should be unchanged
        assert claude_local.read_text() == user_content


# ===========================================================================
# Scenario 3: Upgrade migration (user-modified CLAUDE.md, no CLAUDE.local.md)
# ===========================================================================

class TestScenario3UpgradeMigration:
    """Upgrade from old setup: user-modified CLAUDE.md, no CLAUDE.local.md."""

    def test_user_modified_claude_md_migrated_to_local(self, tmp_path):
        """Given user-modified CLAUDE.md and no CLAUDE.local.md, migrate content."""
        project_root = tmp_path / 'myproject'
        project_root.mkdir()
        claude_dir = project_root / '.claude'
        claude_dir.mkdir()

        # Create user-modified CLAUDE.md (doesn't start with # myproject)
        user_claude_md = "# My Custom Project\n\n## Team Rules\nNo tabs allowed."
        (claude_dir / 'CLAUDE.md').write_text(user_claude_md)

        config = {'venv': {'auto_detect': False}, 'stack': 'python'}

        with patch('pactkit.generators.deployer.Path.cwd', return_value=project_root):
            _deployer()._generate_project_claude_md(config)

        # User content should be migrated to CLAUDE.local.md
        claude_local = claude_dir / 'CLAUDE.local.md'
        assert claude_local.exists()
        local_content = claude_local.read_text()
        assert 'My Custom Project' in local_content
        assert 'Team Rules' in local_content

        # CLAUDE.md should be regenerated
        claude_md_content = (claude_dir / 'CLAUDE.md').read_text()
        assert '# myproject' in claude_md_content

    def test_migration_heuristic_different_project_name(self, tmp_path):
        """Detect user modification: file doesn't start with # {project_name}."""
        project_root = tmp_path / 'myproject'
        project_root.mkdir()
        claude_dir = project_root / '.claude'
        claude_dir.mkdir()

        # File starts with different project name = user modified
        (claude_dir / 'CLAUDE.md').write_text("# SomeOtherProject\nUser content")

        config = {'venv': {'auto_detect': False}, 'stack': 'python'}

        with patch('pactkit.generators.deployer.Path.cwd', return_value=project_root):
            _deployer()._generate_project_claude_md(config)

        # Should detect as user-modified and migrate
        local_content = (claude_dir / 'CLAUDE.local.md').read_text()
        assert 'SomeOtherProject' in local_content


# ===========================================================================
# Scenario 4: Upgrade migration (unmodified PactKit CLAUDE.md, no CLAUDE.local.md)
# ===========================================================================

class TestScenario4UpgradeNoMigration:
    """Upgrade from old setup: unmodified PactKit template, no CLAUDE.local.md."""

    def test_unmodified_template_not_migrated(self, tmp_path):
        """Given unmodified PactKit CLAUDE.md, create empty CLAUDE.local.md."""
        project_root = tmp_path / 'myproject'
        project_root.mkdir()
        claude_dir = project_root / '.claude'
        claude_dir.mkdir()

        # Create unmodified PactKit template (starts with # myproject)
        pactkit_template = """# myproject — Project Context

## Dev Commands

```bash
# Run tests
pytest tests/ -v
```

@./docs/product/context.md
"""
        (claude_dir / 'CLAUDE.md').write_text(pactkit_template)

        config = {'venv': {'auto_detect': False}, 'stack': 'python'}

        with patch('pactkit.generators.deployer.Path.cwd', return_value=project_root):
            _deployer()._generate_project_claude_md(config)

        # CLAUDE.local.md should be created with empty template (no migration)
        local_content = (claude_dir / 'CLAUDE.local.md').read_text()
        assert 'Project Local Instructions' in local_content
        # Should NOT contain old template content
        assert 'Project Context' not in local_content


# ===========================================================================
# Scenario 5: HOME directory guard
# ===========================================================================

class TestScenario5HomeGuard:
    """HOME directory guard prevents writing to home directory."""

    def test_home_directory_guard(self, tmp_path):
        """Given cwd equals home, no files are written."""
        # Create minimal structure
        claude_dir = tmp_path / '.claude'
        claude_dir.mkdir()

        config = {'venv': {'auto_detect': False}, 'stack': 'python'}

        # Mock both cwd and home to be the same
        with patch('pactkit.generators.deployer.Path.cwd', return_value=tmp_path):
            with patch('pactkit.generators.deployer.Path.home', return_value=tmp_path):
                _deployer()._generate_project_claude_md(config)

        # No files should be created
        claude_md = claude_dir / 'CLAUDE.md'
        claude_local = claude_dir / 'CLAUDE.local.md'
        assert not claude_md.exists()
        assert not claude_local.exists()


# ===========================================================================
# Scenario 6: Preview mode guard (tested at _deploy_classic level)
# ===========================================================================

class TestScenario6PreviewModeGuard:
    """Preview mode guard: _generate_project_claude_md is NOT called when target is set."""

    def test_preview_mode_does_not_call_generate(self, tmp_path):
        """Given target is set (preview mode), _generate_project_claude_md is NOT called."""
        # This is tested at the _deploy_classic level
        # Create minimal config
        project_yaml = tmp_path / '.claude' / 'pactkit.yaml'
        project_yaml.parent.mkdir(parents=True)
        project_yaml.write_text("skills: []\nrules: []\nagents: []\ncommands: []")

        # Create a real project to check that nothing is written there
        real_project = tmp_path / 'real_project'
        real_project.mkdir()
        real_claude_dir = real_project / '.claude'

        preview_target = tmp_path / 'preview'

        with patch('pactkit.generators.deployer.Path.cwd', return_value=real_project):
            # Deploy to preview target (NOT None)
            _deployer()._deploy_classic(target=str(preview_target))

        # Real project should NOT have CLAUDE.md created
        assert not real_claude_dir.exists() or not (real_claude_dir / 'CLAUDE.md').exists()


# ===========================================================================
# R1: Function renamed and always regenerates
# ===========================================================================

class TestR1FunctionRenamedAndAlwaysRegenerates:
    """R1: Function is renamed and always regenerates CLAUDE.md."""

    def test_function_exists_with_new_name(self):
        """The function should be named _generate_project_claude_md (no _if_missing)."""
        deployer = _deployer()
        assert hasattr(deployer, '_generate_project_claude_md')
        # Old name should not exist (or should be removed)
        # Note: We might keep it as alias for backward compatibility in tests

    def test_always_overwrites_claude_md(self, tmp_path):
        """CLAUDE.md is always overwritten, even if it exists."""
        project_root = tmp_path / 'myproject'
        project_root.mkdir()
        claude_dir = project_root / '.claude'
        claude_dir.mkdir()

        # Create existing CLAUDE.md
        claude_md = claude_dir / 'CLAUDE.md'
        original = "# Original content that should be replaced"
        claude_md.write_text(original)

        # Also create CLAUDE.local.md to avoid migration
        (claude_dir / 'CLAUDE.local.md').write_text("# Local")

        config = {'venv': {'auto_detect': False}, 'stack': 'python'}

        with patch('pactkit.generators.deployer.Path.cwd', return_value=project_root):
            _deployer()._generate_project_claude_md(config)

        # CLAUDE.md should be overwritten
        new_content = claude_md.read_text()
        assert original not in new_content
        assert '# myproject' in new_content


# ===========================================================================
# R5: Global CLAUDE.md behavior unchanged
# ===========================================================================

class TestR5GlobalClaudeMdUnchanged:
    """R5: _deploy_claude_md (global) behavior must remain unchanged."""

    def test_global_claude_md_always_overwrites(self, tmp_path):
        """Global CLAUDE.md at ~/.claude is always overwritten."""
        claude_root = tmp_path
        rules_dir = claude_root / 'rules'
        rules_dir.mkdir()

        # Create existing global CLAUDE.md
        claude_md = claude_root / 'CLAUDE.md'
        claude_md.write_text("# Old global content")

        # Call global deploy function (not project-level)
        enabled_rules = ['01-core-protocol']
        _deployer()._deploy_claude_md(claude_root, enabled_rules)

        # Should be overwritten
        content = claude_md.read_text()
        assert 'Old global content' not in content
        assert 'PactKit Global Constitution' in content


# ===========================================================================
# R3: CLAUDE.local.md created only if missing
# ===========================================================================

class TestR3ClaudeLocalCreatedOnlyIfMissing:
    """R3: _generate_claude_local_md_if_missing creates file only when missing."""

    def test_creates_when_missing(self, tmp_path):
        """If CLAUDE.local.md doesn't exist, create it."""
        project_root = tmp_path / 'myproject'
        project_root.mkdir()
        claude_dir = project_root / '.claude'
        claude_dir.mkdir()

        _deployer()._generate_claude_local_md_if_missing(claude_dir)

        local_md = claude_dir / 'CLAUDE.local.md'
        assert local_md.exists()
        content = local_md.read_text()
        assert 'Project Local Instructions' in content

    def test_does_not_modify_existing(self, tmp_path):
        """If CLAUDE.local.md exists, do NOT modify it."""
        project_root = tmp_path / 'myproject'
        project_root.mkdir()
        claude_dir = project_root / '.claude'
        claude_dir.mkdir()

        # Create existing file with user content
        local_md = claude_dir / 'CLAUDE.local.md'
        user_content = "# User's custom content\nDo NOT touch!"
        local_md.write_text(user_content)

        _deployer()._generate_claude_local_md_if_missing(claude_dir)

        # Should be unchanged
        assert local_md.read_text() == user_content
