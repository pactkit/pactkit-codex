"""
STORY-046: Multi-Agent Compatibility Layer
Tests for the agent format adapter that transforms Claude Code playbooks
to other agent formats (cursor, copilot, generic).
"""
import warnings

# ===========================================================================
# R1: Import / Module Structure
# ===========================================================================

class TestR1Importable:
    """Adapter module is importable and exposes required symbols."""

    def test_import_adapter_module(self):
        """Adapter module is importable from pactkit.generators.adapter."""
        from pactkit.generators.adapter import (  # noqa: F401
            SUPPORTED_AGENTS,
            get_file_extension,
            get_target_dir,
            strip_frontmatter,
            transform,
        )

    def test_supported_agents_contains_claude(self):
        from pactkit.generators.adapter import SUPPORTED_AGENTS
        assert 'claude' in SUPPORTED_AGENTS

    def test_supported_agents_contains_cursor(self):
        from pactkit.generators.adapter import SUPPORTED_AGENTS
        assert 'cursor' in SUPPORTED_AGENTS

    def test_supported_agents_contains_copilot(self):
        from pactkit.generators.adapter import SUPPORTED_AGENTS
        assert 'copilot' in SUPPORTED_AGENTS

    def test_supported_agents_contains_generic(self):
        from pactkit.generators.adapter import SUPPORTED_AGENTS
        assert 'generic' in SUPPORTED_AGENTS


# ===========================================================================
# R3: transform() function
# ===========================================================================

SAMPLE_CONTENT_WITH_FRONTMATTER = """\
---
description: "Test command"
allowed-tools: [Read, Write]
---

# Command: Test

This is the body of the command.
"""

SAMPLE_CONTENT_WITHOUT_FRONTMATTER = """\
# Command: Test

This is the body of the command.
"""


class TestR3TransformClaude:
    """transform('claude') returns content unchanged."""

    def test_transform_claude_returns_unchanged(self):
        from pactkit.generators.adapter import transform
        content = SAMPLE_CONTENT_WITH_FRONTMATTER
        result = transform(content, 'claude')
        assert result == content

    def test_transform_claude_no_frontmatter_unchanged(self):
        from pactkit.generators.adapter import transform
        content = SAMPLE_CONTENT_WITHOUT_FRONTMATTER
        result = transform(content, 'claude')
        assert result == content


class TestR3TransformCursor:
    """transform('cursor') strips YAML frontmatter block."""

    def test_transform_cursor_strips_frontmatter(self):
        from pactkit.generators.adapter import transform
        result = transform(SAMPLE_CONTENT_WITH_FRONTMATTER, 'cursor')
        assert '---' not in result.split('\n')[0]
        assert 'description:' not in result
        assert 'allowed-tools:' not in result

    def test_transform_cursor_body_preserved(self):
        from pactkit.generators.adapter import transform
        result = transform(SAMPLE_CONTENT_WITH_FRONTMATTER, 'cursor')
        assert '# Command: Test' in result
        assert 'This is the body of the command.' in result

    def test_transform_cursor_no_frontmatter_content_preserved(self):
        from pactkit.generators.adapter import transform
        result = transform(SAMPLE_CONTENT_WITHOUT_FRONTMATTER, 'cursor')
        assert '# Command: Test' in result


class TestR3TransformCopilot:
    """transform('copilot') strips frontmatter and returns plain body."""

    def test_transform_copilot_strips_frontmatter(self):
        from pactkit.generators.adapter import transform
        result = transform(SAMPLE_CONTENT_WITH_FRONTMATTER, 'copilot')
        assert 'description:' not in result
        assert 'allowed-tools:' not in result

    def test_transform_copilot_body_preserved(self):
        from pactkit.generators.adapter import transform
        result = transform(SAMPLE_CONTENT_WITH_FRONTMATTER, 'copilot')
        assert '# Command: Test' in result
        assert 'This is the body of the command.' in result


class TestR3TransformGeneric:
    """transform('generic') strips frontmatter and returns plain body."""

    def test_transform_generic_strips_frontmatter(self):
        from pactkit.generators.adapter import transform
        result = transform(SAMPLE_CONTENT_WITH_FRONTMATTER, 'generic')
        assert 'description:' not in result
        assert 'allowed-tools:' not in result

    def test_transform_generic_body_preserved(self):
        from pactkit.generators.adapter import transform
        result = transform(SAMPLE_CONTENT_WITH_FRONTMATTER, 'generic')
        assert '# Command: Test' in result
        assert 'This is the body of the command.' in result


# ===========================================================================
# strip_frontmatter()
# ===========================================================================

class TestStripFrontmatter:
    """strip_frontmatter removes the --- block from the top."""

    def test_basic_strip(self):
        from pactkit.generators.adapter import strip_frontmatter
        content = "---\nkey: val\n---\nbody"
        result = strip_frontmatter(content)
        assert 'key:' not in result
        assert 'body' in result

    def test_strip_leaves_body_intact(self):
        from pactkit.generators.adapter import strip_frontmatter
        content = "---\nfoo: bar\nbaz: qux\n---\n\n# Title\n\nContent here."
        result = strip_frontmatter(content)
        assert '# Title' in result
        assert 'Content here.' in result
        assert 'foo:' not in result

    def test_no_frontmatter_unchanged(self):
        from pactkit.generators.adapter import strip_frontmatter
        content = "# Title\n\nContent here."
        result = strip_frontmatter(content)
        assert '# Title' in result
        assert 'Content here.' in result

    def test_empty_string(self):
        from pactkit.generators.adapter import strip_frontmatter
        result = strip_frontmatter("")
        assert result == ""

    def test_only_frontmatter_returns_empty_or_minimal(self):
        from pactkit.generators.adapter import strip_frontmatter
        content = "---\nkey: val\n---\n"
        result = strip_frontmatter(content)
        # After stripping, should not contain frontmatter keys
        assert 'key:' not in result


# ===========================================================================
# get_target_dir()
# ===========================================================================

class TestGetTargetDir:
    """get_target_dir returns correct path for each agent."""

    def test_cursor_dir_contains_cursor_rules(self):
        from pactkit.generators.adapter import get_target_dir
        result = get_target_dir('cursor')
        assert '.cursor/rules' in result

    def test_copilot_dir_contains_github(self):
        from pactkit.generators.adapter import get_target_dir
        result = get_target_dir('copilot')
        assert '.github' in result

    def test_generic_dir_contains_ai_commands(self):
        from pactkit.generators.adapter import get_target_dir
        result = get_target_dir('generic')
        assert '.ai/commands' in result

    def test_claude_dir_contains_claude_commands(self):
        from pactkit.generators.adapter import get_target_dir
        result = get_target_dir('claude')
        assert '.claude' in result or 'claude' in result.lower()

    def test_unknown_agent_returns_fallback(self):
        from pactkit.generators.adapter import get_target_dir
        result = get_target_dir('unknown_agent')
        # Should return some path, not raise
        assert isinstance(result, str)


# ===========================================================================
# get_file_extension()
# ===========================================================================

class TestGetFileExtension:
    """get_file_extension returns correct extension per agent."""

    def test_cursor_extension_is_mdc(self):
        from pactkit.generators.adapter import get_file_extension
        assert get_file_extension('cursor') == '.mdc'

    def test_claude_extension_is_md(self):
        from pactkit.generators.adapter import get_file_extension
        assert get_file_extension('claude') == '.md'

    def test_copilot_extension_is_md(self):
        from pactkit.generators.adapter import get_file_extension
        assert get_file_extension('copilot') == '.md'

    def test_generic_extension_is_md(self):
        from pactkit.generators.adapter import get_file_extension
        assert get_file_extension('generic') == '.md'


# ===========================================================================
# R4: Config round-trip — multi_agent field
# ===========================================================================

class TestR4ConfigMultiAgent:
    """pactkit.yaml with multi_agent field does not raise validation error."""

    def test_validate_config_accepts_multi_agent(self, tmp_path):
        """Config with multi_agent list does not raise or warn about it."""
        from pactkit.config import load_config, validate_config

        yaml_content = """\
version: "0.0.1"
stack: python
agents:
  - senior-developer
commands:
  - project-act
skills:
  - pactkit-visualize
rules:
  - 01-core-protocol
multi_agent:
  - cursor
  - copilot
"""
        yaml_path = tmp_path / 'pactkit.yaml'
        yaml_path.write_text(yaml_content)

        config = load_config(yaml_path)
        # Should not raise; multi_agent is an unknown but accepted key
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            validate_config(config)

        # No warnings about multi_agent specifically
        multi_agent_warnings = [
            w for w in caught
            if 'multi_agent' in str(w.message).lower()
        ]
        assert len(multi_agent_warnings) == 0

    def test_load_config_preserves_multi_agent(self, tmp_path):
        """load_config preserves multi_agent list from YAML."""
        from pactkit.config import load_config

        yaml_content = """\
version: "0.0.1"
stack: python
agents: []
commands: []
skills: []
rules: []
multi_agent:
  - cursor
  - copilot
"""
        yaml_path = tmp_path / 'pactkit.yaml'
        yaml_path.write_text(yaml_content)

        config = load_config(yaml_path)
        assert config.get('multi_agent') == ['cursor', 'copilot']
