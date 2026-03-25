"""
STORY-045: Auto-PR Enhancement
Updated by STORY-051: Phase 4.2 Auto-PR extracted from project-done.md
into standalone project-pr.md command.

Tests for:
- PR generation logic now lives in project-pr.md (standalone command)
- project-done.md prompts user to run /project-pr after commit
"""


def _commands():
    from pactkit.prompts import COMMANDS_CONTENT
    return COMMANDS_CONTENT


# ===========================================================================
# Phase 4.2 extracted to project-pr.md (STORY-051)
# ===========================================================================

class TestDonePhase42AutoPR:
    """STORY-051: Phase 4.2 was extracted to project-pr.md. Done prompts user to run /project-pr."""

    def test_phase_42_exists_in_done(self):
        """STORY-051: Phase 4.2 removed from Done; project-pr.md is the standalone command."""
        content = _commands()["project-pr.md"]
        assert "PR" in content or "pull request" in content.lower()

    def test_phase_42_mentions_auto_pr(self):
        """PR functionality is now in project-pr.md."""
        content = _commands()["project-pr.md"]
        assert "PR" in content or "pull request" in content.lower()

    def test_phase_42_mentions_main_master_skip(self):
        """project-pr.md skips when on main/master branch."""
        content = _commands()["project-pr.md"]
        has_main_skip = (
            "main" in content and "master" in content
            and ("skip" in content.lower() or "Skip" in content or "STOP" in content)
        )
        assert has_main_skip

    def test_phase_42_mentions_existing_pr_check(self):
        """project-pr.md checks for an existing open PR."""
        content = _commands()["project-pr.md"]
        assert "gh pr list" in content

    def test_phase_42_mentions_user_confirmation(self):
        """project-pr.md asks user for confirmation before creating PR."""
        content = _commands()["project-pr.md"]
        has_confirmation = (
            "yes/no" in content
            or "yes/no/edit" in content
            or "confirmation" in content.lower()
            or ("yes" in content and "no" in content and "edit" in content)
        )
        assert has_confirmation

    def test_phase_42_mentions_gh_cli_fallback(self):
        """project-pr.md handles gh CLI being unavailable."""
        content = _commands()["project-pr.md"]
        has_fallback = (
            "gh CLI" in content
            or "gh` CLI" in content
            or "gh cli" in content.lower()
        ) and (
            "unavailable" in content
            or "not available" in content
            or "skip" in content.lower()
            or "STOP" in content
        )
        assert has_fallback

    def test_phase_42_mentions_pr_body_structure(self):
        """project-pr.md defines a PR body with Summary, Changes, and Acceptance Criteria."""
        content = _commands()["project-pr.md"]
        has_summary = "Summary" in content
        has_changes = "Changes" in content
        has_ac = "Acceptance Criteria" in content
        assert has_summary and has_changes and has_ac

    def test_phase_42_is_between_phase_4_and_phase_45(self):
        """STORY-051: Phase 4.2 removed from Done; Done prompts user to run /project-pr."""
        done = _commands()["project-done.md"]
        pr_cmd = _commands()["project-pr.md"]
        # Done should no longer contain Phase 4.2
        assert "Phase 4.2" not in done, "Phase 4.2 must be removed from Done"
        # Done should prompt the user to run /project-pr
        assert "project-pr" in done, "Done must prompt user to run /project-pr"
        # project-pr.md should exist with PR content
        assert "gh pr create" in pr_cmd or "Pull Request" in pr_cmd or "PR" in pr_cmd
