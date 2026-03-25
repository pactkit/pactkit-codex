"""
STORY-056: Security Check Scope Filtering — Commands prompt content tests

Verify:
- R1: Plan Phase 3 generates Security Scope section in Spec
- R1.1: Detection rules map SEC-1..SEC-8 to file/code patterns
- R1.2: Docs/tests-only shortcut marks all checks N/A
- R1.3: Security Scope section format with Applicable column
- R2: Check Phase 0 reads Security Scope from Spec
- R2.2: Fallback behavior for legacy Specs (no Security Scope section)
- R3: Check Phase 1 only executes Applicable=Yes checks
- R3.1: SKIPPED output for Applicable=No/N/A checks
- R4.2: check.security_scope_override config referenced in Check prompt
"""
import importlib


def _commands():
    from pactkit.prompts import commands as cmd
    importlib.reload(cmd)
    return cmd


# ===========================================================================
# R1: Plan Phase — Security Scope generation
# ===========================================================================

class TestPlanSecurityScopeGeneration:
    """Plan Phase 3 MUST generate a ## Security Scope section in the Spec."""

    def _plan(self) -> str:
        return _commands().COMMANDS_CONTENT['project-plan.md']

    def test_plan_mentions_security_scope(self):
        """R1.3: Plan must include instructions to generate Security Scope section."""
        plan = self._plan()
        assert 'Security Scope' in plan, \
            "project-plan.md must mention 'Security Scope' section generation"

    def test_plan_security_scope_has_applicable_column(self):
        """R1.3: Security Scope table must have an Applicable column."""
        plan = self._plan()
        assert 'Applicable' in plan, \
            "Security Scope table format must include 'Applicable' column"

    def test_plan_security_scope_has_reason_column(self):
        """R1.3: Security Scope table must have a Reason column."""
        plan = self._plan()
        assert 'Reason' in plan, \
            "Security Scope table format must include 'Reason' column"

    def test_plan_mentions_sec1_detection_rule(self):
        """R1.1: Detection rule for SEC-1 (source code files)."""
        plan = self._plan()
        # SEC-1 is applicable when source code files are modified
        assert 'SEC-1' in plan, \
            "Plan must include SEC-1 detection rule for Security Scope"

    def test_plan_mentions_sec8_detection_rule(self):
        """R1.1: Detection rule for SEC-8 (dependency files)."""
        plan = self._plan()
        assert 'SEC-8' in plan, \
            "Plan must include SEC-8 detection rule for Security Scope"

    def test_plan_mentions_docs_only_shortcut(self):
        """R1.2: Docs/tests-only changes should mark ALL checks N/A."""
        plan = self._plan()
        assert 'docs' in plan.lower() or 'doc' in plan.lower(), \
            "Plan must mention docs-only shortcut for Security Scope"
        # N/A must be present for the docs-only shortcut
        assert 'N/A' in plan or 'n/a' in plan.lower(), \
            "Plan must reference N/A for docs-only Security Scope"

    def test_plan_security_scope_is_in_phase3(self):
        """R1.3: Security Scope generation should be part of Plan Phase 3 (Spec)."""
        plan = self._plan()
        # Phase 3 contains the Spec creation instructions
        phase3_idx = plan.find('Phase 3')
        security_scope_idx = plan.find('Security Scope')
        assert phase3_idx != -1, "Plan must have a Phase 3"
        assert security_scope_idx != -1, "Plan must mention Security Scope"
        # Security Scope instructions must appear in or after Phase 3
        assert security_scope_idx >= phase3_idx, \
            "Security Scope generation must appear in Plan Phase 3 or later"


# ===========================================================================
# R2: Check Phase 0 — Scope reading
# ===========================================================================

class TestCheckPhase0ScopeReading:
    """Check Phase 0 MUST read the Security Scope from the Spec."""

    def _check(self) -> str:
        return _commands().COMMANDS_CONTENT['project-check.md']

    def test_check_phase0_mentions_security_scope(self):
        """R2.1: Check Phase 0 must parse Security Scope if present."""
        check = self._check()
        assert 'Security Scope' in check, \
            "project-check.md Phase 0 must mention Security Scope reading"

    def test_check_mentions_legacy_fallback(self):
        """R2.2: If Security Scope section is missing, fall back to run all checks."""
        check = self._check()
        # Must mention fallback behavior for legacy specs
        assert 'fallback' in check.lower() or 'legacy' in check.lower() or \
               'missing' in check.lower() or 'absent' in check.lower(), \
            "Check must describe fallback behavior when Security Scope is absent (R2.2)"

    def test_check_scope_passed_to_phase1(self):
        """R2.3: Parsed scope must be passed to Phase 1 Security Scan."""
        check = self._check()
        # The prompt must connect Phase 0 scope reading to Phase 1 filtering
        assert 'Applicable' in check or 'scope' in check.lower(), \
            "Check must pass scope information to Phase 1 (R2.3)"


# ===========================================================================
# R3: Check Phase 1 — Filtered execution
# ===========================================================================

class TestCheckPhase1FilteredExecution:
    """Check Phase 1 MUST only execute checks marked Applicable=Yes."""

    def _check(self) -> str:
        return _commands().COMMANDS_CONTENT['project-check.md']

    def test_check_phase1_references_skipped_output(self):
        """R3.1: Checks marked No or N/A must output SKIPPED."""
        check = self._check()
        assert 'SKIPPED' in check, \
            "Check Phase 1 must output 'SKIPPED' for non-applicable checks (R3.1)"

    def test_check_phase1_skipped_includes_reason(self):
        """R3.1: SKIPPED output must include reason."""
        check = self._check()
        skipped_idx = check.find('SKIPPED')
        assert skipped_idx != -1, "SKIPPED must appear in check prompt"
        # After SKIPPED, there should be a reason reference
        context = check[skipped_idx:skipped_idx + 100]
        assert 'reason' in context.lower() or '(' in context, \
            "SKIPPED output must include reason (e.g., 'SKIPPED (no database code)')"

    def test_check_phase1_references_applicable(self):
        """R3.2: Phase 1 must reference Applicable=Yes checks to execute."""
        check = self._check()
        assert 'Applicable' in check, \
            "Check Phase 1 must reference 'Applicable' status from Security Scope"

    def test_check_verdict_shows_full_checklist(self):
        """R3.3: Verdict must include full checklist showing both executed and skipped."""
        check = self._check()
        # The verdict Security Checklist table must still show all SEC-* items
        assert 'Security Checklist' in check, \
            "Check Verdict must show full Security Checklist table (R3.3)"

    def test_check_references_security_scope_override(self):
        """R4.2: check.security_scope_override: full must force all checks to run."""
        check = self._check()
        assert 'security_scope_override' in check, \
            "Check must reference security_scope_override config option (R4.2)"
