"""
BUG-021: Generated project CLAUDE.md ignores LANG_PROFILES, hardcodes Unix paths,
         and contradicts Playbook.
"""
from unittest.mock import patch

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _config():
    from pactkit import config
    return config


def _deployer():
    from pactkit.generators import deployer
    return deployer


# ===========================================================================
# R1: Always Regenerate CLAUDE.md (STORY-040 supersedes BUG-021)
# ===========================================================================

class TestR1AlwaysRegenerate:
    """STORY-040: CLAUDE.md is always regenerated, user content migrated to CLAUDE.local.md."""

    def test_existing_file_regenerated_with_migration(self, tmp_path):
        """Given .claude/CLAUDE.md exists (user-modified), it is regenerated and content migrated."""
        # Setup: create project with existing user-modified CLAUDE.md
        project_root = tmp_path / 'myproject'
        project_root.mkdir()
        claude_dir = project_root / '.claude'
        claude_dir.mkdir()

        original_content = "# User's custom CLAUDE.md\nDo not touch this."
        claude_md_path = claude_dir / 'CLAUDE.md'
        claude_md_path.write_text(original_content)

        # Create minimal config
        config = {'venv': {'auto_detect': True}, 'stack': 'python'}

        # Call the function
        with patch('pactkit.generators.deployer.Path.cwd', return_value=project_root):
            _deployer()._generate_project_claude_md_if_missing(config)

        # STORY-040: CLAUDE.md is regenerated (framework content)
        new_content = claude_md_path.read_text()
        assert '# myproject' in new_content
        # User content migrated to CLAUDE.local.md
        local_content = (claude_dir / 'CLAUDE.local.md').read_text()
        assert "User's custom CLAUDE.md" in local_content

    def test_no_backup_created_when_exists(self, tmp_path):
        """When file exists, no .bak file should be created (migration goes to CLAUDE.local.md)."""
        project_root = tmp_path / 'myproject'
        project_root.mkdir()
        claude_dir = project_root / '.claude'
        claude_dir.mkdir()

        claude_md_path = claude_dir / 'CLAUDE.md'
        claude_md_path.write_text("# Existing")

        config = {'venv': {'auto_detect': True}, 'stack': 'python'}

        with patch('pactkit.generators.deployer.Path.cwd', return_value=project_root):
            _deployer()._generate_project_claude_md_if_missing(config)

        # Assert: no .bak backup file created (STORY-040 uses CLAUDE.local.md instead)
        backup_path = claude_dir / 'CLAUDE.md.bak'
        assert not backup_path.exists()


class TestR1GenerateWhenMissing:
    """AC2: If .claude/CLAUDE.md does NOT exist, generate it."""

    def test_generates_when_missing(self, tmp_path):
        """Given .claude/CLAUDE.md does not exist, it should be created."""
        project_root = tmp_path / 'myproject'
        project_root.mkdir()
        claude_dir = project_root / '.claude'
        claude_dir.mkdir()

        # Create a Unix venv
        venv_dir = project_root / '.venv' / 'bin'
        venv_dir.mkdir(parents=True)
        (venv_dir / 'python3').write_text('')

        config = {'venv': {'auto_detect': True}, 'stack': 'python'}

        with patch('pactkit.generators.deployer.Path.cwd', return_value=project_root):
            _deployer()._generate_project_claude_md_if_missing(config)

        claude_md_path = claude_dir / 'CLAUDE.md'
        assert claude_md_path.exists()
        content = claude_md_path.read_text()
        assert 'source .venv/bin/activate' in content


# ===========================================================================
# R2: Platform-Aware Venv Commands (AC2-AC3, AC7-AC8)
# ===========================================================================

class TestR2DetectVenvWithLayout:
    """AC7-AC8: detect_venv returns both directory name and layout."""

    def test_detect_venv_unix_layout(self, tmp_path):
        """Given Unix venv structure, return ('name', 'unix')."""
        project_root = tmp_path
        venv_dir = project_root / '.venv' / 'bin'
        venv_dir.mkdir(parents=True)
        (venv_dir / 'python3').write_text('')

        result = _config().detect_venv(project_root)
        # After fix, should return tuple (name, layout)
        assert isinstance(result, tuple)
        assert result[0] == '.venv'
        assert result[1] == 'unix'

    def test_detect_venv_windows_layout(self, tmp_path):
        """Given Windows venv structure, return ('name', 'windows')."""
        project_root = tmp_path
        venv_dir = project_root / 'venv' / 'Scripts'
        venv_dir.mkdir(parents=True)
        (venv_dir / 'python.exe').write_text('')

        result = _config().detect_venv(project_root)
        # After fix, should return tuple (name, layout)
        assert isinstance(result, tuple)
        assert result[0] == 'venv'
        assert result[1] == 'windows'

    def test_detect_venv_none_when_missing(self, tmp_path):
        """Given no venv, return None."""
        result = _config().detect_venv(tmp_path)
        assert result is None


class TestR2PlatformAwareCommands:
    """AC2-AC3: Generated CLAUDE.md uses correct paths for detected platform."""

    def test_unix_venv_commands(self, tmp_path):
        """Unix venv should generate source ... /bin/activate commands."""
        project_root = tmp_path / 'myproject'
        project_root.mkdir()
        claude_dir = project_root / '.claude'
        claude_dir.mkdir()

        # Create Unix venv
        venv_dir = project_root / '.venv' / 'bin'
        venv_dir.mkdir(parents=True)
        (venv_dir / 'python3').write_text('')

        config = {'venv': {'auto_detect': True}, 'stack': 'python'}

        with patch('pactkit.generators.deployer.Path.cwd', return_value=project_root):
            _deployer()._generate_project_claude_md_if_missing(config)

        content = (claude_dir / 'CLAUDE.md').read_text()
        assert 'source .venv/bin/activate' in content
        assert '.venv/bin/python3' in content
        assert 'Scripts' not in content

    def test_windows_venv_commands(self, tmp_path):
        """Windows venv should generate Scripts-based commands, no 'source'."""
        project_root = tmp_path / 'myproject'
        project_root.mkdir()
        claude_dir = project_root / '.claude'
        claude_dir.mkdir()

        # Create Windows venv
        venv_dir = project_root / '.venv' / 'Scripts'
        venv_dir.mkdir(parents=True)
        (venv_dir / 'python.exe').write_text('')

        config = {'venv': {'auto_detect': True}, 'stack': 'python'}

        with patch('pactkit.generators.deployer.Path.cwd', return_value=project_root):
            _deployer()._generate_project_claude_md_if_missing(config)

        content = (claude_dir / 'CLAUDE.md').read_text()
        # Windows should NOT use 'source ... /bin/activate'
        assert 'source .venv/bin/activate' not in content
        # Should use Scripts path
        assert '.venv/Scripts/python.exe' in content or '.venv\\Scripts\\python.exe' in content


# ===========================================================================
# R3: Stack-Aware Lint Command (AC4-AC6)
# ===========================================================================

class TestR3StackAwareLint:
    """Lint command comes from LANG_PROFILES based on stack."""

    def test_node_stack_uses_eslint(self, tmp_path):
        """AC4: stack=node → lint command is 'npx eslint .'"""
        project_root = tmp_path / 'myproject'
        project_root.mkdir()
        claude_dir = project_root / '.claude'
        claude_dir.mkdir()

        config = {'venv': {'auto_detect': False}, 'stack': 'node'}

        with patch('pactkit.generators.deployer.Path.cwd', return_value=project_root):
            _deployer()._generate_project_claude_md_if_missing(config)

        content = (claude_dir / 'CLAUDE.md').read_text()
        assert 'npx eslint' in content
        assert 'ruff check' not in content

    def test_go_stack_uses_golangci_lint(self, tmp_path):
        """AC5: stack=go → lint command is 'golangci-lint run'"""
        project_root = tmp_path / 'myproject'
        project_root.mkdir()
        claude_dir = project_root / '.claude'
        claude_dir.mkdir()

        config = {'venv': {'auto_detect': False}, 'stack': 'go'}

        with patch('pactkit.generators.deployer.Path.cwd', return_value=project_root):
            _deployer()._generate_project_claude_md_if_missing(config)

        content = (claude_dir / 'CLAUDE.md').read_text()
        assert 'golangci-lint run' in content
        assert 'ruff check' not in content

    def test_auto_stack_falls_back_to_python(self, tmp_path):
        """AC6: stack=auto → lint command is Python's ruff."""
        project_root = tmp_path / 'myproject'
        project_root.mkdir()
        claude_dir = project_root / '.claude'
        claude_dir.mkdir()

        config = {'venv': {'auto_detect': False}, 'stack': 'auto'}

        with patch('pactkit.generators.deployer.Path.cwd', return_value=project_root):
            _deployer()._generate_project_claude_md_if_missing(config)

        content = (claude_dir / 'CLAUDE.md').read_text()
        assert 'ruff check src/ tests/' in content


# ===========================================================================
# R4: Stack-Aware Test Runner (AC4-AC6)
# ===========================================================================

class TestR4StackAwareTestRunner:
    """Test runner command comes from LANG_PROFILES."""

    def test_node_stack_uses_jest(self, tmp_path):
        """AC4: stack=node → test runner is 'npx jest'"""
        project_root = tmp_path / 'myproject'
        project_root.mkdir()
        claude_dir = project_root / '.claude'
        claude_dir.mkdir()

        config = {'venv': {'auto_detect': False}, 'stack': 'node'}

        with patch('pactkit.generators.deployer.Path.cwd', return_value=project_root):
            _deployer()._generate_project_claude_md_if_missing(config)

        content = (claude_dir / 'CLAUDE.md').read_text()
        assert 'npx jest' in content
        assert 'pytest' not in content

    def test_go_stack_uses_go_test(self, tmp_path):
        """AC5: stack=go → test runner is 'go test ./...'"""
        project_root = tmp_path / 'myproject'
        project_root.mkdir()
        claude_dir = project_root / '.claude'
        claude_dir.mkdir()

        config = {'venv': {'auto_detect': False}, 'stack': 'go'}

        with patch('pactkit.generators.deployer.Path.cwd', return_value=project_root):
            _deployer()._generate_project_claude_md_if_missing(config)

        content = (claude_dir / 'CLAUDE.md').read_text()
        assert 'go test' in content
        assert 'pytest' not in content

    def test_python_venv_prefixes_test_runner(self, tmp_path):
        """Python with venv → test runner prefixed with venv path."""
        project_root = tmp_path / 'myproject'
        project_root.mkdir()
        claude_dir = project_root / '.claude'
        claude_dir.mkdir()

        # Create Unix venv
        venv_dir = project_root / '.venv' / 'bin'
        venv_dir.mkdir(parents=True)
        (venv_dir / 'python3').write_text('')

        config = {'venv': {'auto_detect': True}, 'stack': 'python'}

        with patch('pactkit.generators.deployer.Path.cwd', return_value=project_root):
            _deployer()._generate_project_claude_md_if_missing(config)

        content = (claude_dir / 'CLAUDE.md').read_text()
        assert '.venv/bin/pytest' in content


# ===========================================================================
# R5: Backward Compatibility
# ===========================================================================

class TestR5BackwardCompatibility:
    """Projects without venv still get valid CLAUDE.md."""

    def test_no_venv_generates_valid_claude_md(self, tmp_path):
        """Without venv, generate CLAUDE.md with bare commands."""
        project_root = tmp_path / 'myproject'
        project_root.mkdir()
        claude_dir = project_root / '.claude'
        claude_dir.mkdir()

        config = {'venv': {'auto_detect': True}, 'stack': 'python'}

        with patch('pactkit.generators.deployer.Path.cwd', return_value=project_root):
            _deployer()._generate_project_claude_md_if_missing(config)

        content = (claude_dir / 'CLAUDE.md').read_text()
        # Should have test command without venv prefix
        assert 'pytest tests/ -v' in content
        # Should NOT have venv section
        assert 'Virtual Environment' not in content

    def test_context_md_reference_preserved(self, tmp_path):
        """Generated CLAUDE.md must include @./docs/product/context.md."""
        project_root = tmp_path / 'myproject'
        project_root.mkdir()
        claude_dir = project_root / '.claude'
        claude_dir.mkdir()

        config = {'venv': {'auto_detect': False}, 'stack': 'python'}

        with patch('pactkit.generators.deployer.Path.cwd', return_value=project_root):
            _deployer()._generate_project_claude_md_if_missing(config)

        content = (claude_dir / 'CLAUDE.md').read_text()
        assert '@./docs/product/context.md' in content
