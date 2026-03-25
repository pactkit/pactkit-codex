"""BUG-slim-006: Post-Migration Cross-Flow Residual Gaps — Graphs, Board Schema, HOTFIX ID."""
from pathlib import Path
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _get_board() -> str:
    return (PROJECT_ROOT / "docs/product/sprint_board.md").read_text()


def _get_hotfix_prompt() -> str:
    from pactkit.prompts.workflows import HOTFIX_PROMPT

    return HOTFIX_PROMPT


def _get_lang_profiles() -> dict:
    from pactkit.prompts.workflows import LANG_PROFILES

    return LANG_PROFILES


def _get_rules() -> str:
    return (PROJECT_ROOT / "docs/architecture/governance/rules.md").read_text()


def _get_system_design() -> str:
    return (PROJECT_ROOT / "docs/architecture/graphs/system_design.mmd").read_text()


def _get_done_prompt() -> str:
    from pactkit.prompts import COMMANDS_CONTENT

    return COMMANDS_CONTENT["project-done.md"]


# =========================================================================
# AC1: Board schema compliance
# =========================================================================
class TestAC1BoardSchema:
    def test_board_has_backlog_section(self):
        board = _get_board()
        assert "## 📋 Backlog" in board

    def test_board_has_in_progress_section(self):
        board = _get_board()
        assert "## 🔄 In Progress" in board

    def test_board_has_done_section(self):
        board = _get_board()
        assert "## ✅ Done" in board

    def test_board_sections_in_order(self):
        board = _get_board()
        backlog_idx = board.index("## 📋 Backlog")
        in_progress_idx = board.index("## 🔄 In Progress")
        done_idx = board.index("## ✅ Done")
        assert backlog_idx < in_progress_idx < done_idx


# =========================================================================
# AC2: HOTFIX next-id --prefix removed
# =========================================================================
class TestAC2HotfixNextId:
    def test_no_prefix_flag_in_hotfix(self):
        hotfix = _get_hotfix_prompt()
        assert "--prefix" not in hotfix

    def test_hotfix_still_references_next_id(self):
        hotfix = _get_hotfix_prompt()
        assert "pactkit next-id" in hotfix or "HOTFIX-" in hotfix


# =========================================================================
# AC5: ADR-008 in table (no blank line between ADR-007 and ADR-008)
# =========================================================================
class TestAC5AdrTableFormatting:
    def test_adr008_follows_adr007_no_blank_line(self):
        rules = _get_rules()
        lines = rules.split("\n")
        adr007_idx = None
        adr008_idx = None
        for i, line in enumerate(lines):
            if "ADR-007" in line:
                adr007_idx = i
            if "ADR-008" in line:
                adr008_idx = i
        assert adr007_idx is not None, "ADR-007 not found"
        assert adr008_idx is not None, "ADR-008 not found"
        assert adr008_idx == adr007_idx + 1, (
            f"ADR-008 at line {adr008_idx}, expected {adr007_idx + 1} (no blank line)"
        )


# =========================================================================
# AC3: pactkit visualize --lazy executes graph generation
# =========================================================================
class TestAC3LazyVisualizeExecutor:
    def test_lazy_visualize_calls_run_visualize_graphs(self):
        """cli.py visualize --lazy MUST invoke run_visualize_graphs (not just print)."""
        from pactkit.cli import main as cli_main

        with patch("pactkit.lazy_visualize.should_visualize", return_value=(True, "source files changed")):
            with patch("pactkit.lazy_visualize.run_visualize_graphs") as mock_run:
                import sys
                old_argv = sys.argv
                try:
                    sys.argv = ["pactkit", "visualize", "--lazy"]
                    try:
                        cli_main()
                    except SystemExit:
                        pass
                finally:
                    sys.argv = old_argv
                assert mock_run.call_count == 1, (
                    f"Expected run_visualize_graphs to be called once, got {mock_run.call_count}"
                )

    def test_run_visualize_graphs_invokes_all_modes(self):
        """run_visualize_graphs MUST run file, class, call modes via subprocess."""
        from pactkit.lazy_visualize import run_visualize_graphs

        with patch("pactkit.lazy_visualize.subprocess.run") as mock_run:
            mock_run.return_value = type("R", (), {"returncode": 0, "stdout": "", "stderr": ""})()
            run_visualize_graphs(PROJECT_ROOT)
            calls = [str(c) for c in mock_run.call_args_list]
            viz_calls = [c for c in calls if "visualize.py" in c]
            assert len(viz_calls) >= 3, (
                f"Expected >=3 visualize.py calls (file,class,call), got {len(viz_calls)}"
            )

    def test_lazy_visualize_skips_when_no_changes(self):
        """When should_visualize returns False, no graph generation occurs."""
        from pactkit.cli import main as cli_main

        with patch("pactkit.lazy_visualize.should_visualize", return_value=(False, "Graph up-to-date")):
            with patch("pactkit.lazy_visualize.run_visualize_graphs") as mock_run:
                import sys
                old_argv = sys.argv
                try:
                    sys.argv = ["pactkit", "visualize", "--lazy"]
                    try:
                        cli_main()
                    except SystemExit:
                        pass
                finally:
                    sys.argv = old_argv
                assert mock_run.call_count == 0, "Should not run visualize when no changes"


# =========================================================================
# AC4: pactkit doctor reports HLD drift
# =========================================================================
class TestAC4DoctorHldDrift:
    def test_check_hld_module_count_returns_drift(self):
        from pactkit.doctor import check_hld_module_count

        result = check_hld_module_count(PROJECT_ROOT)
        assert "source_modules" in result
        assert "hld_nodes" in result
        assert "drift" in result
        assert isinstance(result["drift"], int)

    def test_check_hld_module_count_detects_modules(self):
        from pactkit.doctor import check_hld_module_count

        result = check_hld_module_count(PROJECT_ROOT)
        # We know src/pactkit has 20+ modules
        assert result["source_modules"] >= 20, f"Expected >=20 source modules, got {result['source_modules']}"


# =========================================================================
# AC8: system_design.mmd has CLI subcommand modules
# =========================================================================
class TestAC8SystemDesign:
    def test_has_cli_subcommand_subgraph(self):
        design = _get_system_design()
        assert "CLI" in design
        for module in ["doctor", "lessons", "coverage_gate", "guards", "validators"]:
            assert module in design.lower(), f"system_design.mmd missing {module}"


# =========================================================================
# AC9: Done prompt uses pactkit doctor for HLD check
# =========================================================================
class TestAC9DonePromptDoctorRef:
    def test_done_phase2_references_pactkit_doctor(self):
        done = _get_done_prompt()
        assert "pactkit doctor" in done, "Done Phase 2 must reference 'pactkit doctor' for HLD check"


# =========================================================================
# AC7: LANG_PROFILES cleanup key removed
# =========================================================================
class TestAC7CleanupKeyRemoved:
    PROFILES = ["python", "node", "go", "java"]

    def test_no_cleanup_key_in_any_profile(self):
        profiles = _get_lang_profiles()
        for lang in self.PROFILES:
            assert "cleanup" not in profiles[lang], (
                f"LANG_PROFILES[{lang}] still has 'cleanup' key"
            )

    def test_profiles_have_5_consumed_keys(self):
        """After removing cleanup, each profile should have 5 keys."""
        profiles = _get_lang_profiles()
        from pactkit.schemas import LANG_PROFILE_REQUIRED_KEYS
        expected = LANG_PROFILE_REQUIRED_KEYS
        for lang in self.PROFILES:
            assert set(profiles[lang].keys()) == expected, (
                f"LANG_PROFILES[{lang}] keys: {set(profiles[lang].keys())} != {expected}"
            )
