"""
BUG-025: project-release 与 pactkit-release 功能重复且不一致

Verify:
- AC1: project-release.md does NOT contain inline snapshot/tag logic; MUST reference pactkit-release
- AC2: After refactor, /project-release provides all capabilities of pactkit-release
- AC3: pactkit-release skill auto-detects version when not provided (backward compat)
"""
import importlib


def _commands():
    import pactkit.prompts.commands as c
    importlib.reload(c)
    return c


def _skills():
    from pactkit.prompts import skills as sk
    importlib.reload(sk)
    return sk


# ===========================================================================
# AC1: Single Implementation — no inline logic in command
# ===========================================================================

class TestProjectReleaseNoDuplication:
    """project-release.md MUST NOT contain inline snapshot/archive/tag logic."""

    def _release_cmd(self):
        return _commands().COMMANDS_CONTENT['project-release.md']

    def test_no_inline_snapshot_command(self):
        """board.py snapshot should NOT appear inline in the command."""
        cmd = self._release_cmd()
        assert 'board.py snapshot' not in cmd, \
            "project-release.md must delegate to pactkit-release, not call board.py snapshot directly"

    def test_no_inline_archive_command(self):
        """board.py archive should NOT appear inline in the command."""
        cmd = self._release_cmd()
        assert 'board.py archive' not in cmd, \
            "project-release.md must delegate to pactkit-release, not call board.py archive directly"

    def test_no_inline_git_tag(self):
        """git tag should NOT appear inline in the command."""
        cmd = self._release_cmd()
        assert 'git tag' not in cmd, \
            "project-release.md must delegate to pactkit-release, not create git tags directly"

    def test_references_pactkit_release_skill(self):
        """project-release.md MUST reference pactkit-release skill."""
        cmd = self._release_cmd()
        assert 'pactkit-release' in cmd, \
            "project-release.md must invoke the pactkit-release skill"

    def test_preflight_phase_preserved(self):
        """Phase 0 pre-flight check MUST remain in the command."""
        cmd = self._release_cmd()
        assert 'Phase 0' in cmd or 'Pre-flight' in cmd or 'pre-flight' in cmd.lower(), \
            "project-release.md must retain the pre-flight check phase"

    def test_command_stops_on_no_version_bump(self):
        """Command MUST stop if no version bump detected."""
        cmd = self._release_cmd()
        assert 'STOP' in cmd or 'stop' in cmd.lower(), \
            "project-release.md must STOP when no version bump is detected"

    def test_no_github_release_inline(self):
        """gh release create should NOT be inline in the command (delegated to skill)."""
        cmd = self._release_cmd()
        assert 'gh release create' not in cmd, \
            "project-release.md must not have inline gh release create (delegated to skill)"


# ===========================================================================
# AC2: Full release flow — skill has all capabilities
# ===========================================================================

class TestPactKitReleaseFullFlow:
    """pactkit-release SKILL must provide complete release capabilities."""

    def _skill(self):
        return _skills().SKILL_RELEASE_MD

    def test_skill_has_version_update(self):
        """Skill must have version update step."""
        skill = self._skill()
        assert 'update_version' in skill or 'Version Update' in skill, \
            "pactkit-release skill must include version update"

    def test_skill_has_spec_backfill(self):
        """Skill must backfill Specs Release: TBD."""
        skill = self._skill()
        assert 'backfill' in skill.lower() or 'Backfill' in skill or 'TBD' in skill, \
            "pactkit-release skill must backfill Spec release fields"

    def test_skill_has_snapshot(self):
        """Skill must create architecture snapshots."""
        skill = self._skill()
        assert 'snapshot' in skill.lower(), \
            "pactkit-release skill must create snapshots"

    def test_skill_has_archive(self):
        """Skill must archive completed stories."""
        skill = self._skill()
        assert 'archive' in skill.lower(), \
            "pactkit-release skill must archive stories"

    def test_skill_has_git_tag(self):
        """Skill must create a git tag."""
        skill = self._skill()
        assert 'git tag' in skill or 'Tag' in skill, \
            "pactkit-release skill must create a git tag"

    def test_skill_has_github_release(self):
        """Skill must create a GitHub Release."""
        skill = self._skill()
        assert 'gh release' in skill or 'GitHub Release' in skill, \
            "pactkit-release skill must create a GitHub Release"


# ===========================================================================
# AC3: Backward compatible — skill auto-detects version
# ===========================================================================

class TestVersionAutoDetection:
    """pactkit-release skill MUST auto-detect version when not provided."""

    def _skill(self):
        return _skills().SKILL_RELEASE_MD

    def test_skill_handles_version_not_provided(self):
        """Skill must describe behavior when VERSION is not provided."""
        skill = self._skill()
        # Should mention auto-detection fallback
        assert ('not provided' in skill or 'auto-detect' in skill.lower()
                or 'pyproject.toml' in skill), \
            "pactkit-release skill must handle version auto-detection"

    def test_skill_version_is_optional(self):
        """Skill must accept optional version parameter."""
        skill = self._skill()
        assert 'optional' in skill.lower() or 'if not provided' in skill.lower() \
               or 'If version' in skill or 'if version' in skill.lower(), \
            "pactkit-release skill must document that version is optional"
