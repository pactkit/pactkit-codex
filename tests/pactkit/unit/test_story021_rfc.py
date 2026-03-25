"""STORY-021: Spec Amendment Protocol (RFC Mechanism)."""
import re

from pactkit.prompts.commands import COMMANDS_CONTENT
from pactkit.prompts.rules import RULES_MODULES


class TestRFCInActPrompt:
    """project-act Phase 0 must include RFC clause."""

    def _act_prompt(self):
        return COMMANDS_CONTENT["project-act.md"]

    def test_rfc_keyword_present(self):
        """R1: Act prompt must mention RFC Protocol."""
        prompt = self._act_prompt()
        assert "RFC" in prompt

    def test_infeasible_trigger(self):
        """R1: Must mention infeasible/contradictory as trigger."""
        prompt = self._act_prompt()
        assert re.search(r"infeasible|contradictory", prompt, re.IGNORECASE)

    def test_stop_on_rfc(self):
        """R2: Must STOP implementation when RFC is triggered."""
        prompt = self._act_prompt()
        assert re.search(r"RFC.{0,200}STOP", prompt, re.IGNORECASE | re.DOTALL)

    def test_report_to_user(self):
        """R2: Must report which requirement is problematic."""
        prompt = self._act_prompt()
        assert re.search(r"(report|quote).{0,100}(requirement|Spec)", prompt, re.IGNORECASE)

    def test_no_unilateral_spec_modification(self):
        """R2: Agent must NOT modify Spec unilaterally."""
        prompt = self._act_prompt()
        assert re.search(r"(MUST NOT|must not|do not).{0,50}modify.{0,30}Spec", prompt, re.IGNORECASE)


class TestHierarchyOfTruthAmendment:
    """Rule 02 must have RFC exception clause."""

    def _hierarchy_rule(self):
        return RULES_MODULES["hierarchy"]

    def test_rfc_exception_in_hierarchy(self):
        """R3: Hierarchy rule must mention RFC Protocol."""
        rule = self._hierarchy_rule()
        assert "RFC" in rule

    def test_infeasible_exception_clause(self):
        """R3: Must have an exception for infeasible Specs."""
        rule = self._hierarchy_rule()
        assert re.search(r"infeasible|technically impossible", rule, re.IGNORECASE)

    def test_spec_authority_preserved(self):
        """S4: General principle Spec > Code must still be present."""
        rule = self._hierarchy_rule()
        assert "Spec takes precedence" in rule or "Spec wins" in rule
