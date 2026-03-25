"""
STORY-055: PDCA Quality Gates Enhancement — Commands prompt content tests

Verify:
- R1: Plan Phase 3 Spec template includes Implementation Steps guidance
- R2: Check Phase 1 has structured 8-item security checklist (SEC-1 to SEC-8)
- R2.2: Checklist items reference PASS/FAIL/N/A output format
- R2.3: FAIL on SEC-1..SEC-5 classified as P0
- R2.4: Results included in Phase 5 / Verdict
- R2.5: Checklist can be disabled via check.security_checklist config
- R3: Done Phase 3.3 has 5-dimension lesson quality scoring
- R3.3 + R3.4: Threshold gate with default 15
- R3.5: Log message when lesson skipped
- R3.6: Score appended to lesson row
- R3.7: P0/P1 findings receive bonus
"""
import importlib


def _commands():
    from pactkit.prompts import commands as cmd
    importlib.reload(cmd)
    return cmd


# ===========================================================================
# R1: Plan Phase — Implementation Steps template
# ===========================================================================

class TestPlanImplementationStepsTemplate:
    """Plan Phase 3 MUST guide the agent to add an Implementation Steps section."""

    def _plan(self) -> str:
        return _commands().COMMANDS_CONTENT['project-plan.md']

    def test_plan_mentions_implementation_steps(self):
        plan = self._plan()
        assert 'Implementation Steps' in plan, \
            "project-plan.md must mention 'Implementation Steps' section"

    def test_plan_implementation_steps_has_table_guidance(self):
        """Plan must guide agent about Implementation Steps table (inline or via scaffold)."""
        plan = self._plan()
        # STORY-slim-026: table format moved to SPEC_TEMPLATE; prompt references skeleton
        assert 'table' in plan.lower() or 'skeleton' in plan.lower() or 'Dependencies' in plan, \
            "Implementation Steps guidance must mention table format (inline or via scaffold)"


# ===========================================================================
# R2: Check Phase — Structured Security Checklist
# ===========================================================================

class TestCheckSecurityChecklist:
    """Check Phase 1 MUST have a structured 8-item security checklist."""

    def _check(self) -> str:
        return _commands().COMMANDS_CONTENT['project-check.md']

    def test_check_has_sec1_secrets(self):
        check = self._check()
        assert 'SEC-1' in check, "Check must include SEC-1 (Secrets check)"

    def test_check_has_sec2_input(self):
        check = self._check()
        assert 'SEC-2' in check, "Check must include SEC-2 (Input validation)"

    def test_check_has_sec3_sql(self):
        check = self._check()
        assert 'SEC-3' in check, "Check must include SEC-3 (SQL injection)"

    def test_check_has_sec4_xss(self):
        check = self._check()
        assert 'SEC-4' in check, "Check must include SEC-4 (XSS)"

    def test_check_has_sec5_auth(self):
        check = self._check()
        assert 'SEC-5' in check, "Check must include SEC-5 (Auth tokens)"

    def test_check_has_sec6_rate(self):
        check = self._check()
        assert 'SEC-6' in check, "Check must include SEC-6 (Rate limiting)"

    def test_check_has_sec7_error(self):
        check = self._check()
        assert 'SEC-7' in check, "Check must include SEC-7 (Error messages)"

    def test_check_has_sec8_deps(self):
        check = self._check()
        assert 'SEC-8' in check, "Check must include SEC-8 (Dependencies/CVEs)"

    def test_check_mentions_pass_fail_na(self):
        """R2.2: Each item must output PASS, FAIL, or N/A."""
        check = self._check()
        assert 'PASS' in check and 'FAIL' in check, \
            "Check security checklist must reference PASS and FAIL outputs"
        assert 'N/A' in check or 'N/A' in check, \
            "Check security checklist must reference N/A for non-applicable items"

    def test_check_sec1_to_sec5_fail_is_p0(self):
        """R2.3: FAIL on SEC-1..SEC-5 must be classified as P0."""
        check = self._check()
        assert 'P0' in check, \
            "Check must classify SEC-1..SEC-5 FAIL as P0 Critical"

    def test_check_results_in_verdict(self):
        """R2.4: Results must be included in Phase 5 Verdict."""
        check = self._check()
        assert 'Security Checklist' in check or 'security_checklist' in check, \
            "Check Verdict section must reference Security Checklist results"

    def test_check_can_be_disabled_via_config(self):
        """R2.5: Checklist must be disableable via check.security_checklist: false."""
        check = self._check()
        assert 'security_checklist' in check, \
            "Check must reference check.security_checklist config option"


# ===========================================================================
# R3: Done Phase — Lesson Quality Scoring
# ===========================================================================

class TestDoneLessonQualityGate:
    """Done Phase 3.3 MUST have a simple lesson quality gate."""

    def _done(self) -> str:
        return _commands().COMMANDS_CONTENT['project-done.md']

    def test_done_has_specificity_check(self):
        """Lesson must reference concrete file/function/pattern."""
        done = self._done()
        assert 'specific' in done.lower() or 'concrete' in done.lower(), \
            "Done must check lesson specificity"

    def test_done_has_duplicate_check(self):
        """Lesson must not duplicate existing entries."""
        done = self._done()
        assert 'duplicate' in done.lower() or 'different' in done.lower(), \
            "Done must check for duplicate lessons"

    def test_done_has_skip_log_message(self):
        """Must log when lesson is skipped."""
        done = self._done()
        assert 'skipped' in done.lower() or 'Lesson skipped' in done, \
            "Done must log when lesson is skipped"

    def test_done_lesson_row_format(self):
        """Appended lesson row must have date, summary, story ID."""
        done = self._done()
        assert 'YYYY-MM-DD' in done and 'STORY_ID' in done, \
            "Done lesson row format must include date and story ID"
