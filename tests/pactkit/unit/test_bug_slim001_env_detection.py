"""BUG-slim-001: project-init must detect environment before calling pactkit init.

Verifies that the project-init playbook:
1. Detects environment BEFORE calling pactkit init/update
2. Uses --format opencode when OpenCode is detected
3. Does NOT instruct creating .claude/ in OpenCode environment
4. Uses environment-aware SKILLS_PATH instead of hardcoded ~/.claude/skills/
"""

import unittest


class TestBugSlim001PlaybookEnvironmentDetection(unittest.TestCase):
    """Verify project-init playbook contains environment detection before pactkit init."""

    def _get_init_playbook(self):
        from pactkit.prompts.commands import COMMANDS_CONTENT

        return COMMANDS_CONTENT["project-init.md"]

    def test_environment_detection_before_pactkit_init(self):
        """DETECTED_ENV must be set before any pactkit init call."""
        playbook = self._get_init_playbook()
        detect_pos = playbook.find("DETECTED_ENV")
        pactkit_init_pos = playbook.find("pactkit init --format opencode")
        self.assertGreater(detect_pos, -1, "DETECTED_ENV not found in playbook")
        self.assertGreater(pactkit_init_pos, -1, "--format opencode not found in playbook")
        self.assertLess(
            detect_pos, pactkit_init_pos, "DETECTED_ENV must appear before 'pactkit init --format opencode'"
        )

    def test_opencode_format_flag_present(self):
        """Playbook must include --format opencode for OpenCode environment."""
        playbook = self._get_init_playbook()
        self.assertIn("pactkit init --format opencode", playbook)
        self.assertIn("pactkit update --format opencode", playbook)

    def test_no_hardcoded_claude_skills_path(self):
        """Playbook must NOT have hardcoded ~/.claude/skills/ paths (use $SKILLS_PATH)."""
        playbook = self._get_init_playbook()
        # After Phase 1, all skill paths should use $SKILLS_PATH variable
        phase2_onwards = playbook[playbook.find("Phase 2") :]
        self.assertNotIn(
            "~/.claude/skills/",
            phase2_onwards,
            "Found hardcoded ~/.claude/skills/ in Phase 2+. Use $SKILLS_PATH instead.",
        )

    def test_no_unconditional_claude_dir_creation(self):
        """Playbook must NOT unconditionally create .claude/ directory."""
        playbook = self._get_init_playbook()
        # The playbook should only create .claude/ when DETECTED_ENV=classic
        self.assertIn("DETECTED_ENV=classic", playbook)
        self.assertIn("DETECTED_ENV=opencode", playbook)
        # Ensure .claude/CLAUDE.md creation is conditional on classic
        claude_md_section = playbook[playbook.find("Project Instructions File") :]
        self.assertIn(
            "DETECTED_ENV=classic", claude_md_section, "CLAUDE.md creation must be conditional on DETECTED_ENV=classic"
        )

    def test_skills_path_variable_used(self):
        """Playbook must use $SKILLS_PATH variable for skill script invocations."""
        playbook = self._get_init_playbook()
        self.assertIn("SKILLS_PATH", playbook)
        self.assertIn("$SKILLS_PATH/pactkit-visualize", playbook)
        self.assertIn("$SKILLS_PATH/pactkit-scaffold", playbook)


if __name__ == "__main__":
    unittest.main()
