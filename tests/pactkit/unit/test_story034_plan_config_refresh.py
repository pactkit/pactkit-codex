"""
STORY-034: Auto-refresh pactkit.yaml in Plan Init Guard.

Tests verify that Plan Phase 0.5 includes a config completeness check
step that detects stale configs and runs `pactkit update` to backfill.
"""

from pactkit.prompts import COMMANDS_CONTENT


# ===========================================================================
# AC4: Prompt template updated — Phase 0.5 includes config completeness check
# ===========================================================================
class TestAC4PromptTemplateUpdated:
    """Plan command Phase 0.5 must include a config completeness check step."""

    # Use the Phase 1 *header* as boundary (not inline "Phase 1" text)
    _PHASE1_HEADER = "Phase 1: Archaeology"

    def _plan(self):
        return COMMANDS_CONTENT["project-plan.md"]

    def _phase05_text(self):
        """Extract Phase 0.5 section text (between header and Phase 1 header)."""
        content = self._plan()
        start = content.index("Phase 0.5")
        end = content.index(self._PHASE1_HEADER)
        return content[start:end]

    # --- Step existence ---

    def test_phase05_mentions_config_completeness(self):
        """Phase 0.5 must mention checking config completeness."""
        text = self._phase05_text().lower()
        assert "config" in text and ("completeness" in text or "missing" in text)

    def test_phase05_references_pactkit_update(self):
        """Phase 0.5 must reference `pactkit update` as the refresh mechanism."""
        assert "pactkit update" in self._phase05_text()

    def test_pactkit_update_in_phase05_not_phase1(self):
        """`pactkit update` reference must appear within Phase 0.5, before Phase 1."""
        assert "pactkit update" in self._phase05_text()

    # --- Known section names ---

    def test_phase05_lists_known_sections(self):
        """Phase 0.5 must mention the known section names to check against."""
        text = self._phase05_text().lower()
        assert "hooks" in text
        assert "ci" in text

    # --- Stale detection flow ---

    def test_phase05_describes_stale_detection(self):
        """Phase 0.5 must describe how stale config is detected."""
        text = self._phase05_text().lower()
        assert "missing" in text or "stale" in text

    def test_phase05_describes_refresh_action(self):
        """Phase 0.5 must describe running pactkit update when stale."""
        text = self._phase05_text()
        assert "pactkit update" in text
        lower = text.lower()
        assert "run" in lower or "execute" in lower

    # --- Idempotency / skip when complete ---

    def test_phase05_mentions_skip_when_complete(self):
        """Phase 0.5 must mention skipping refresh when config is already complete."""
        text = self._phase05_text().lower()
        assert "skip" in text or "complete" in text or "up to date" in text

    # --- Reporting ---

    def test_phase05_mentions_reporting_what_was_added(self):
        """Phase 0.5 must mention reporting what sections were added."""
        text = self._phase05_text().lower()
        assert "report" in text or "added" in text or "refresh" in text

    # --- Ordering: config check after marker check ---

    def test_config_check_after_marker_check(self):
        """Config completeness check must appear after the marker existence check."""
        text = self._phase05_text()
        marker_pos = text.index("pactkit.yaml")
        update_pos = text.index("pactkit update")
        assert marker_pos < update_pos

    # --- Existing Init Guard preserved ---

    def test_existing_marker_checks_preserved(self):
        """Original 3 marker checks must still be present (STORY-slim-006: pactkit.yaml via template var)."""
        content = self._plan()
        # pactkit.yaml check now uses {PACTKIT_YAML} template variable
        assert "{PACTKIT_YAML}" in content or "pactkit.yaml" in content
        assert "docs/product/sprint_board.md" in content
        assert "docs/architecture/graphs/" in content

    def test_project_init_trigger_preserved(self):
        """Original /project-init trigger must still be present."""
        text = self._phase05_text()
        assert "/project-init" in text
