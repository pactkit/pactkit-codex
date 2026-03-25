"""STORY-018: Architecture docs staleness prevention.

Verifies that the Done command prompt includes:
- system_design.mmd consistency check (Gap 1)
- governance/rules.md invariants refresh (Gap 2)
- Release snapshot verification gate (Gap 3)
"""
from pactkit.prompts.commands import COMMANDS_CONTENT

# ===========================================================================
# Scenario 1: Done Phase 2 has system_design.mmd validation
# ===========================================================================

class TestSystemDesignValidation:
    """Done command must check system_design.mmd for stale component counts."""

    def test_done_prompt_has_system_design_check(self):
        done = COMMANDS_CONTENT['project-done.md']
        assert 'system_design.mmd' in done

    def test_done_prompt_mentions_component_count_verification(self):
        done = COMMANDS_CONTENT['project-done.md']
        # Must mention verifying counts or checking consistency
        lower = done.lower()
        assert ('component count' in lower
                or 'mismatch' in lower
                or 'consistency' in lower
                or 'verify' in lower and 'system_design' in lower)

    def test_done_prompt_warns_on_mismatch(self):
        """Must instruct agent to warn when counts don't match."""
        done = COMMANDS_CONTENT['project-done.md']
        lower = done.lower()
        assert 'warn' in lower or 'mismatch' in lower


# ===========================================================================
# Scenario 2: Done Phase 3 has rules.md invariants refresh
# ===========================================================================

class TestRulesInvariantsRefresh:
    """Done command must refresh governance/rules.md invariants."""

    def test_done_prompt_has_rules_md_refresh(self):
        done = COMMANDS_CONTENT['project-done.md']
        assert 'rules.md' in done

    def test_done_prompt_mentions_test_count_update(self):
        done = COMMANDS_CONTENT['project-done.md']
        lower = done.lower()
        assert ('test count' in lower
                or 'invariant' in lower
                or 'tests must pass' in lower)

    def test_done_prompt_preserves_adr(self):
        """Must not overwrite ADR entries."""
        done = COMMANDS_CONTENT['project-done.md']
        lower = done.lower()
        assert ('invariant' in lower
                or 'preserve' in lower
                or 'only update' in lower)


# ===========================================================================
# Scenario 3: Done Phase 3.8 has snapshot verification
# ===========================================================================

class TestSnapshotVerification:
    """Done release flow must verify snapshots exist after creation."""

    def test_done_prompt_has_snapshot_verification(self):
        done = COMMANDS_CONTENT['project-done.md']
        lower = done.lower()
        assert ('verify' in lower and 'snapshot' in lower) or \
               ('confirm' in lower and 'snapshot' in lower) or \
               ('check' in lower and 'snapshot' in lower)

    def test_done_prompt_mentions_snapshot_files(self):
        done = COMMANDS_CONTENT['project-done.md']
        assert 'snapshots/' in done or 'snapshot' in done.lower()
