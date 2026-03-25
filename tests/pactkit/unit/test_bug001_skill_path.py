"""Tests for BUG-001: Scripted Skill Prompts Use Wrong Script Path.

Verifies that SKILL_VISUALIZE_MD, SKILL_BOARD_MD, and SKILL_SCAFFOLD_MD
reference scripts using the skill base directory, not bare relative paths.
"""
import re

from pactkit.prompts.skills import (
    SKILL_BOARD_MD,
    SKILL_SCAFFOLD_MD,
    SKILL_VISUALIZE_MD,
)

# The 3 scripted skill templates to check
SCRIPTED_SKILLS = {
    'SKILL_VISUALIZE_MD': (SKILL_VISUALIZE_MD, 'visualize.py'),
    'SKILL_BOARD_MD': (SKILL_BOARD_MD, 'board.py'),
    'SKILL_SCAFFOLD_MD': (SKILL_SCAFFOLD_MD, 'scaffold.py'),
}


class TestNoBarePaths:
    """TC-1/2/3: No bare scripts/ paths without base directory anchor."""

    def test_visualize_no_bare_path(self):
        """SKILL_VISUALIZE_MD must not use bare 'scripts/visualize.py'."""
        # Match "scripts/visualize.py" NOT preceded by a path component
        bare = re.findall(r'(?<![/\w])scripts/visualize\.py', SKILL_VISUALIZE_MD)
        assert len(bare) == 0, (
            f"Found {len(bare)} bare 'scripts/visualize.py' reference(s)"
        )

    def test_board_no_bare_path(self):
        """SKILL_BOARD_MD must not use bare 'scripts/board.py'."""
        bare = re.findall(r'(?<![/\w])scripts/board\.py', SKILL_BOARD_MD)
        assert len(bare) == 0, (
            f"Found {len(bare)} bare 'scripts/board.py' reference(s)"
        )

    def test_scaffold_no_bare_path(self):
        """SKILL_SCAFFOLD_MD must not use bare 'scripts/scaffold.py'."""
        bare = re.findall(r'(?<![/\w])scripts/scaffold\.py', SKILL_SCAFFOLD_MD)
        assert len(bare) == 0, (
            f"Found {len(bare)} bare 'scripts/scaffold.py' reference(s)"
        )


class TestBaseDirectoryInstruction:
    """TC-1/2/3: Prompt includes base directory instruction."""

    def test_visualize_has_base_dir_instruction(self):
        """SKILL_VISUALIZE_MD must reference base directory."""
        assert 'base directory' in SKILL_VISUALIZE_MD.lower() or \
               'Base directory' in SKILL_VISUALIZE_MD, \
               "Missing base directory instruction in SKILL_VISUALIZE_MD"

    def test_board_has_base_dir_instruction(self):
        """SKILL_BOARD_MD must reference base directory."""
        assert 'base directory' in SKILL_BOARD_MD.lower() or \
               'Base directory' in SKILL_BOARD_MD, \
               "Missing base directory instruction in SKILL_BOARD_MD"

    def test_scaffold_has_base_dir_instruction(self):
        """SKILL_SCAFFOLD_MD must reference base directory."""
        assert 'base directory' in SKILL_SCAFFOLD_MD.lower() or \
               'Base directory' in SKILL_SCAFFOLD_MD, \
               "Missing base directory instruction in SKILL_SCAFFOLD_MD"


class TestAbsolutePathPattern:
    """All script invocations use ~/.claude/skills/ absolute path."""

    def test_visualize_uses_absolute_path(self):
        """SKILL_VISUALIZE_MD script commands use absolute path."""
        for m in re.finditer(r'python3\s+\S*visualize\.py', SKILL_VISUALIZE_MD):
            cmd = m.group(0)
            assert '~/.claude/skills/' in cmd or '{base' in cmd.lower(), \
                f"Script invocation without absolute path: {cmd}"

    def test_board_uses_absolute_path(self):
        """SKILL_BOARD_MD script commands use absolute path."""
        for m in re.finditer(r'python3\s+\S*board\.py', SKILL_BOARD_MD):
            cmd = m.group(0)
            assert '~/.claude/skills/' in cmd or '{base' in cmd.lower(), \
                f"Script invocation without absolute path: {cmd}"

    def test_scaffold_uses_absolute_path(self):
        """SKILL_SCAFFOLD_MD script commands use absolute path."""
        for m in re.finditer(r'python3\s+\S*scaffold\.py', SKILL_SCAFFOLD_MD):
            cmd = m.group(0)
            assert '~/.claude/skills/' in cmd or '{base' in cmd.lower(), \
                f"Script invocation without absolute path: {cmd}"
