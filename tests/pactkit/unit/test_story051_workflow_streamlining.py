"""STORY-051: PDCA Workflow Streamlining — verify refactored command prompts."""
import re


def _prompts():
    import importlib

    import pactkit.prompts as p

    importlib.reload(p)
    return p


def _config():
    import importlib

    import pactkit.config as c

    importlib.reload(c)
    return c


# =============================================================================
# AC1 / R1: Done command reduced to ≤9 action phases
# =============================================================================
class TestDoneCommandReduced:
    """AC1: Done command MUST have ≤9 action phases (## 🎬 Phase headers)."""

    def test_done_action_phase_count_le_9(self):
        """Count ## 🎬 Phase sections in Done — must be ≤9."""
        p = _prompts()
        done = p.COMMANDS_CONTENT["project-done.md"]
        action_phases = re.findall(r"## 🎬 Phase", done)
        assert len(action_phases) <= 9, (
            f"Done has {len(action_phases)} action phases, expected ≤9"
        )

    def test_done_no_phase_3_7(self):
        """Phase 3.7 (Deploy & Verify) must be removed from Done."""
        p = _prompts()
        done = p.COMMANDS_CONTENT["project-done.md"]
        assert "Phase 3.7" not in done, "Phase 3.7 must be removed from Done"

    def test_done_no_phase_3_8(self):
        """Phase 3.8 (Release) must be removed from Done."""
        p = _prompts()
        done = p.COMMANDS_CONTENT["project-done.md"]
        assert "Phase 3.8" not in done, "Phase 3.8 must be removed from Done"

    def test_done_no_phase_4_2(self):
        """Phase 4.2 (Auto-PR) must be removed from Done."""
        p = _prompts()
        done = p.COMMANDS_CONTENT["project-done.md"]
        assert "Phase 4.2" not in done, "Phase 4.2 must be removed from Done"

    def test_done_retains_regression_gate(self):
        """Done must still have Regression Gate."""
        p = _prompts()
        done = p.COMMANDS_CONTENT["project-done.md"]
        assert "Regression Gate" in done or "Regression" in done

    def test_done_retains_git_commit(self):
        """Done must still have Git Commit phase."""
        p = _prompts()
        done = p.COMMANDS_CONTENT["project-done.md"]
        assert "Git Commit" in done or "git commit" in done.lower()

    def test_done_retains_archive(self):
        """Done must still have Archive phase."""
        p = _prompts()
        done = p.COMMANDS_CONTENT["project-done.md"]
        assert "Archive" in done

    def test_done_has_release_prompt(self):
        """Done should prompt user to run /project-release for version bumps."""
        p = _prompts()
        done = p.COMMANDS_CONTENT["project-done.md"]
        assert "project-release" in done, (
            "Done must prompt user to run /project-release"
        )

    def test_done_has_pr_prompt(self):
        """Done should prompt user to run /project-pr."""
        p = _prompts()
        done = p.COMMANDS_CONTENT["project-done.md"]
        assert "project-pr" in done, "Done must prompt user to run /project-pr"


# =============================================================================
# AC2 / R1: New standalone commands exist
# =============================================================================
class TestNewCommandsExist:
    """AC2: /project-release and /project-pr MUST be new standalone commands."""

    def test_project_release_in_commands_content(self):
        """project-release.md must be registered in COMMANDS_CONTENT."""
        p = _prompts()
        assert "project-release.md" in p.COMMANDS_CONTENT, (
            "project-release.md not found in COMMANDS_CONTENT"
        )

    def test_project_pr_in_commands_content(self):
        """project-pr.md must be registered in COMMANDS_CONTENT."""
        p = _prompts()
        assert "project-pr.md" in p.COMMANDS_CONTENT, (
            "project-pr.md not found in COMMANDS_CONTENT"
        )

    def test_project_release_has_snapshot_content(self):
        """project-release.md must mention snapshot and git tag."""
        p = _prompts()
        release = p.COMMANDS_CONTENT["project-release.md"]
        lower = release.lower()
        assert "snapshot" in lower, "project-release missing snapshot reference"
        assert "tag" in lower, "project-release missing git tag reference"

    def test_project_pr_has_gh_content(self):
        """project-pr.md must mention gh CLI and PR creation."""
        p = _prompts()
        pr_cmd = p.COMMANDS_CONTENT["project-pr.md"]
        lower = pr_cmd.lower()
        assert "gh" in lower or "pull request" in lower, (
            "project-pr missing gh/PR reference"
        )

    def test_project_release_in_valid_commands(self):
        """project-release must be in VALID_COMMANDS."""
        c = _config()
        assert "project-release" in c.VALID_COMMANDS, (
            "project-release not in VALID_COMMANDS"
        )

    def test_project_pr_in_valid_commands(self):
        """project-pr must be in VALID_COMMANDS."""
        c = _config()
        assert "project-pr" in c.VALID_COMMANDS, "project-pr not in VALID_COMMANDS"

    def test_project_release_not_deprecated(self):
        """project-release must NOT be in DEPRECATED_COMMANDS (it's a new command)."""
        c = _config()
        assert "project-release" not in c.DEPRECATED_COMMANDS, (
            "project-release should not be deprecated — it is a new standalone command"
        )


# =============================================================================
# AC3 / R2: Act no longer has lint check in Phase 3
# =============================================================================
class TestActLintRemoved:
    """AC3: NO lint check should occur in Act Phase 3."""

    def test_act_no_lint_check_in_phase3(self):
        """Act Phase 3 Implementation must not contain Lint Check."""
        p = _prompts()
        act = p.COMMANDS_CONTENT["project-act.md"]
        phase3_idx = act.find("## 🎬 Phase 3: Implementation")
        assert phase3_idx > 0, "Phase 3 Implementation section not found in Act"
        phase4_idx = act.find("## 🎬 Phase 4:", phase3_idx)
        phase3_content = (
            act[phase3_idx:phase4_idx] if phase4_idx > 0 else act[phase3_idx:]
        )
        assert "Lint Check" not in phase3_content, (
            "Lint Check must be removed from Act Phase 3"
        )

    def test_done_still_has_lint_gate(self):
        """Done Phase 2.7 Smart Lint Gate must still exist."""
        p = _prompts()
        done = p.COMMANDS_CONTENT["project-done.md"]
        assert "Lint Gate" in done or "Smart Lint" in done, (
            "Done must still have Lint Gate at Phase 2.7"
        )


# =============================================================================
# AC4 / R3: Lazy visualize
# =============================================================================
class TestLazyVisualize:
    """AC4: visualize SHOULD be skipped for doc-only changes."""

    def test_done_has_lazy_visualize_log(self):
        """Done must include 'Graph up-to-date' skip log message."""
        p = _prompts()
        done = p.COMMANDS_CONTENT["project-done.md"]
        lower = done.lower()
        assert "graph up-to-date" in lower, (
            'Done missing lazy visualize log: "Graph up-to-date — no source changes"'
        )

    def test_done_visualize_references_source_dirs(self):
        """Done lazy visualize must reference source_dirs for detection."""
        p = _prompts()
        done = p.COMMANDS_CONTENT["project-done.md"]
        assert "source_dirs" in done or "LANG_PROFILES" in done, (
            "Done visualize condition must reference source_dirs / LANG_PROFILES"
        )


# =============================================================================
# AC5: All 4 quality gates preserved
# =============================================================================
class TestQualityGatesPreserved:
    """AC5: All 4 quality gates MUST still execute in streamlined workflow."""

    def test_spec_lint_gate_in_act(self):
        """Spec Lint Gate must still be in Act Phase 0.5."""
        p = _prompts()
        act = p.COMMANDS_CONTENT["project-act.md"]
        assert "Spec Lint Gate" in act or "spec_linter" in act, (
            "Spec Lint Gate missing from Act"
        )

    def test_tdd_loop_in_act(self):
        """TDD Loop must still be in Act Phase 3."""
        p = _prompts()
        act = p.COMMANDS_CONTENT["project-act.md"]
        assert "TDD Loop" in act, "TDD Loop missing from Act"

    def test_regression_gate_in_done(self):
        """Regression Gate must still be in Done Phase 2.5."""
        p = _prompts()
        done = p.COMMANDS_CONTENT["project-done.md"]
        assert "Regression Gate" in done, "Regression Gate missing from Done"

    def test_lint_gate_in_done(self):
        """Lint Gate must still be in Done Phase 2.7."""
        p = _prompts()
        done = p.COMMANDS_CONTENT["project-done.md"]
        assert "Lint Gate" in done or "Smart Lint" in done, (
            "Lint Gate missing from Done"
        )


# =============================================================================
# R5: Plan no longer creates Issue Tracker entries
# =============================================================================
class TestPlanIssueTrackerRemoved:
    """R5: Plan MUST NOT create GitHub Issues (moved to Done backfill)."""

    def test_plan_no_issue_creation(self):
        """Plan Phase 3 must not contain gh issue create logic."""
        p = _prompts()
        plan = p.COMMANDS_CONTENT["project-plan.md"]
        assert "gh issue create" not in plan, (
            "Plan must not create GitHub Issues (moved to Done backfill)"
        )

    def test_done_still_has_issue_backfill(self):
        """Done must still have Issue Tracker backfill (Phase 3.5.5)."""
        p = _prompts()
        done = p.COMMANDS_CONTENT["project-done.md"]
        lower = done.lower()
        assert "backfill" in lower or "3.5.5" in done, (
            "Done must still have Issue Tracker backfill at Phase 3.5.5"
        )
