"""Tests for STORY-slim-015: Doctor & Release CLI.

Covers R1-R7: doctor diagnostics, backfill-release, issue-sync, CLI wiring, prompt delegation.
"""
from __future__ import annotations

import shutil
from pathlib import Path
from unittest.mock import patch

# ---------------------------------------------------------------------------
# R1: check_orphaned_specs
# ---------------------------------------------------------------------------

class TestR1OrphanedSpecs:
    """Doctor must cross-reference specs dir vs board + archive."""

    def test_orphaned_spec_detected(self, tmp_path):
        """Spec exists but no board/archive entry → orphaned."""
        from pactkit.doctor import check_orphaned_specs

        specs = tmp_path / "docs" / "specs"
        specs.mkdir(parents=True)
        (specs / "STORY-999.md").write_text("# STORY-999\n")

        board = tmp_path / "docs" / "product" / "sprint_board.md"
        board.parent.mkdir(parents=True)
        board.write_text("# Sprint Board\n## 📋 Backlog\n## ✅ Done\n")

        archive_dir = tmp_path / "docs" / "product" / "archive"
        archive_dir.mkdir(parents=True)

        result = check_orphaned_specs(tmp_path)
        assert "STORY-999" in [r["id"] for r in result["orphaned"]]

    def test_missing_spec_detected(self, tmp_path):
        """Board entry exists but no spec file → missing."""
        from pactkit.doctor import check_orphaned_specs

        specs = tmp_path / "docs" / "specs"
        specs.mkdir(parents=True)

        board = tmp_path / "docs" / "product" / "sprint_board.md"
        board.parent.mkdir(parents=True)
        board.write_text("# Sprint Board\n## 📋 Backlog\n### [STORY-999] Test\n## ✅ Done\n")

        archive_dir = tmp_path / "docs" / "product" / "archive"
        archive_dir.mkdir(parents=True)

        result = check_orphaned_specs(tmp_path)
        assert "STORY-999" in [r["id"] for r in result["missing"]]

    def test_matched_spec_no_issues(self, tmp_path):
        """Spec and board both reference the same ID → no issues."""
        from pactkit.doctor import check_orphaned_specs

        specs = tmp_path / "docs" / "specs"
        specs.mkdir(parents=True)
        (specs / "STORY-001.md").write_text("# STORY-001\n")

        board = tmp_path / "docs" / "product" / "sprint_board.md"
        board.parent.mkdir(parents=True)
        board.write_text("# Sprint Board\n## 📋 Backlog\n### [STORY-001] Test\n## ✅ Done\n")

        archive_dir = tmp_path / "docs" / "product" / "archive"
        archive_dir.mkdir(parents=True)

        result = check_orphaned_specs(tmp_path)
        assert result["orphaned"] == []
        assert result["missing"] == []

    def test_archived_spec_not_orphaned(self, tmp_path):
        """Spec referenced in archive should not be orphaned."""
        from pactkit.doctor import check_orphaned_specs

        specs = tmp_path / "docs" / "specs"
        specs.mkdir(parents=True)
        (specs / "BUG-001.md").write_text("# BUG-001\n")

        board = tmp_path / "docs" / "product" / "sprint_board.md"
        board.parent.mkdir(parents=True)
        board.write_text("# Sprint Board\n## 📋 Backlog\n## ✅ Done\n")

        archive_dir = tmp_path / "docs" / "product" / "archive"
        archive_dir.mkdir(parents=True)
        (archive_dir / "archive_202603.md").write_text("### [BUG-001] Fixed\n- [x] Task\n")

        result = check_orphaned_specs(tmp_path)
        assert result["orphaned"] == []


# ---------------------------------------------------------------------------
# R2: check_config_drift
# ---------------------------------------------------------------------------

class TestR2ConfigDrift:
    """Doctor must detect drift between pactkit.yaml and deployed files."""

    def test_missing_agent_detected(self, tmp_path):
        """Agent listed in config but not deployed → drift."""
        from pactkit.doctor import check_config_drift

        config_dir = tmp_path / ".claude"
        config_dir.mkdir()
        (config_dir / "pactkit.yaml").write_text(
            "agents:\n  - system-architect\n  - missing-agent\ncommands: []\nskills: []\nrules: []\n"
        )
        agents_dir = config_dir / "agents"
        agents_dir.mkdir()
        (agents_dir / "system-architect.md").write_text("# agent\n")

        result = check_config_drift(tmp_path)
        assert any("missing-agent" in d["name"] for d in result["missing_deployments"])

    def test_no_drift_when_all_deployed(self, tmp_path):
        """All configured items deployed → no drift."""
        from pactkit.doctor import check_config_drift

        config_dir = tmp_path / ".claude"
        config_dir.mkdir()
        (config_dir / "pactkit.yaml").write_text(
            "agents:\n  - test-agent\ncommands: []\nskills: []\nrules: []\n"
        )
        agents_dir = config_dir / "agents"
        agents_dir.mkdir()
        (agents_dir / "test-agent.md").write_text("# agent\n")

        result = check_config_drift(tmp_path)
        assert result["missing_deployments"] == []


# ---------------------------------------------------------------------------
# R3: check_stale_graphs
# ---------------------------------------------------------------------------

class TestR3StaleGraphs:
    """Doctor must detect stale .mmd graphs vs source files."""

    def test_stale_graph_detected(self, tmp_path):
        """Graph older than source by > threshold → stale."""
        import os
        import time

        from pactkit.doctor import check_stale_graphs

        # Create source dir with a recent file
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        src_file = src_dir / "app.py"
        src_file.write_text("# code\n")

        # Create old graph
        graph_dir = tmp_path / "docs" / "architecture" / "graphs"
        graph_dir.mkdir(parents=True)
        graph_file = graph_dir / "code_graph.mmd"
        graph_file.write_text("graph TD\n")
        # Set graph mtime to 10 days ago
        old_time = time.time() - (10 * 86400)
        os.utime(graph_file, (old_time, old_time))

        result = check_stale_graphs(tmp_path, threshold_days=7)
        assert any("code_graph.mmd" in g["file"] for g in result["stale"])

    def test_fresh_graph_not_stale(self, tmp_path):
        """Graph modified recently → not stale."""
        from pactkit.doctor import check_stale_graphs

        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "app.py").write_text("# code\n")

        graph_dir = tmp_path / "docs" / "architecture" / "graphs"
        graph_dir.mkdir(parents=True)
        (graph_dir / "code_graph.mmd").write_text("graph TD\n")

        result = check_stale_graphs(tmp_path, threshold_days=7)
        assert result["stale"] == []

    def test_missing_graphs_dir(self, tmp_path):
        """No graphs directory → missing reported."""
        from pactkit.doctor import check_stale_graphs

        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "app.py").write_text("# code\n")

        result = check_stale_graphs(tmp_path, threshold_days=7)
        assert result["missing"]


# ---------------------------------------------------------------------------
# R4: scan_and_replace_tbd
# ---------------------------------------------------------------------------

class TestR4BackfillRelease:
    """backfill-release must replace TBD in completed spec Release fields."""

    def test_replaces_tbd_for_done_story(self, tmp_path):
        """Spec with TBD + done story → replaced."""
        from pactkit.backfill import scan_and_replace_tbd

        specs = tmp_path / "docs" / "specs"
        specs.mkdir(parents=True)
        spec_file = specs / "STORY-014.md"
        spec_file.write_text("| Release | TBD |\n")

        board = tmp_path / "docs" / "product" / "sprint_board.md"
        board.parent.mkdir(parents=True)
        board.write_text(
            "# Sprint Board\n## ✅ Done\n### [STORY-014] Test\n- [x] R1\n"
        )

        archive_dir = tmp_path / "docs" / "product" / "archive"
        archive_dir.mkdir(parents=True)

        result = scan_and_replace_tbd(tmp_path, "2.3.0")
        assert "STORY-014" in [r["id"] for r in result["backfilled"]]
        assert "2.3.0" in spec_file.read_text()
        assert "TBD" not in spec_file.read_text()

    def test_skips_incomplete_story(self, tmp_path):
        """Spec with TBD + incomplete story → skipped."""
        from pactkit.backfill import scan_and_replace_tbd

        specs = tmp_path / "docs" / "specs"
        specs.mkdir(parents=True)
        spec_file = specs / "STORY-015.md"
        spec_file.write_text("| Release | TBD |\n")

        board = tmp_path / "docs" / "product" / "sprint_board.md"
        board.parent.mkdir(parents=True)
        board.write_text(
            "# Sprint Board\n## 📋 Backlog\n### [STORY-015] Test\n- [ ] R1\n## ✅ Done\n"
        )

        archive_dir = tmp_path / "docs" / "product" / "archive"
        archive_dir.mkdir(parents=True)

        result = scan_and_replace_tbd(tmp_path, "2.3.0")
        assert "STORY-015" in [r["id"] for r in result["skipped"]]
        assert "TBD" in spec_file.read_text()

    def test_skips_already_versioned(self, tmp_path):
        """Spec already has version → not touched."""
        from pactkit.backfill import scan_and_replace_tbd

        specs = tmp_path / "docs" / "specs"
        specs.mkdir(parents=True)
        (specs / "STORY-014.md").write_text("| Release | 2.2.0 |\n")

        board = tmp_path / "docs" / "product" / "sprint_board.md"
        board.parent.mkdir(parents=True)
        board.write_text("# Sprint Board\n## ✅ Done\n### [STORY-014] Test\n- [x] R1\n")

        archive_dir = tmp_path / "docs" / "product" / "archive"
        archive_dir.mkdir(parents=True)

        result = scan_and_replace_tbd(tmp_path, "2.3.0")
        assert result["backfilled"] == []

    def test_archived_story_treated_as_done(self, tmp_path):
        """Story in archive (not on board) → treated as done for backfill."""
        from pactkit.backfill import scan_and_replace_tbd

        specs = tmp_path / "docs" / "specs"
        specs.mkdir(parents=True)
        spec_file = specs / "BUG-001.md"
        spec_file.write_text("| Release | TBD |\n")

        board = tmp_path / "docs" / "product" / "sprint_board.md"
        board.parent.mkdir(parents=True)
        board.write_text("# Sprint Board\n## 📋 Backlog\n## ✅ Done\n")

        archive_dir = tmp_path / "docs" / "product" / "archive"
        archive_dir.mkdir(parents=True)
        (archive_dir / "archive_202603.md").write_text("### [BUG-001] Fixed\n- [x] Task\n")

        result = scan_and_replace_tbd(tmp_path, "2.3.0")
        assert "BUG-001" in [r["id"] for r in result["backfilled"]]


# ---------------------------------------------------------------------------
# R5: issue_sync
# ---------------------------------------------------------------------------

class TestR5IssueSync:
    """issue-sync must handle STORY skip, BUG/HOTFIX processing."""

    def test_story_skipped(self, tmp_path):
        """STORY items are skipped for IP protection."""
        from pactkit.issue_sync import issue_sync

        result = issue_sync("STORY-slim-014", tmp_path)
        assert result["action"] == "skipped"
        assert "IP" in result["message"] or "STORY" in result["message"]

    def test_bug_with_no_provider(self, tmp_path):
        """BUG item with no issue_tracker config → skipped."""
        from pactkit.issue_sync import issue_sync

        config_dir = tmp_path / ".claude"
        config_dir.mkdir()
        (config_dir / "pactkit.yaml").write_text("stack: python\n")

        result = issue_sync("BUG-001", tmp_path)
        assert result["action"] == "skipped"

    def test_bug_with_provider_none(self, tmp_path):
        """BUG item with provider: none → skipped."""
        from pactkit.issue_sync import issue_sync

        config_dir = tmp_path / ".claude"
        config_dir.mkdir()
        (config_dir / "pactkit.yaml").write_text(
            "stack: python\nissue_tracker:\n  provider: none\n"
        )

        result = issue_sync("BUG-001", tmp_path)
        assert result["action"] == "skipped"

    @patch("pactkit.issue_sync.subprocess.run")
    def test_bug_with_github_no_gh_cli(self, mock_run, tmp_path):
        """BUG with github provider but no gh CLI → warning."""
        from pactkit.issue_sync import issue_sync

        config_dir = tmp_path / ".claude"
        config_dir.mkdir()
        (config_dir / "pactkit.yaml").write_text(
            "stack: python\nissue_tracker:\n  provider: github\n"
        )

        mock_run.side_effect = FileNotFoundError("gh not found")

        result = issue_sync("BUG-001", tmp_path)
        assert result["action"] == "error"
        assert "unavailable" in result["message"].lower() or "not found" in result["message"].lower()


# ---------------------------------------------------------------------------
# R6: CLI wiring
# ---------------------------------------------------------------------------

class TestR6CLIWiring:
    """CLI must expose doctor, backfill-release, issue-sync subcommands."""

    _PACTKIT = shutil.which("pactkit") or str(Path(__file__).parents[2] / ".venv" / "bin" / "pactkit")

    def test_doctor_subcommand_exists(self):
        """pactkit doctor should be a recognized subcommand."""
        import subprocess
        result = subprocess.run(
            [self._PACTKIT, "doctor", "--help"],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0

    def test_backfill_release_subcommand_exists(self):
        """pactkit backfill-release should be a recognized subcommand."""
        import subprocess
        result = subprocess.run(
            [self._PACTKIT, "backfill-release", "--help"],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0

    def test_issue_sync_subcommand_exists(self):
        """pactkit issue-sync should be a recognized subcommand."""
        import subprocess
        result = subprocess.run(
            [self._PACTKIT, "issue-sync", "--help"],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0


# ---------------------------------------------------------------------------
# R7: Prompt delegation
# ---------------------------------------------------------------------------

class TestR7PromptDelegation:
    """Skills and commands must delegate to new CLI commands."""

    def _reload_prompts(self):
        import importlib

        import pactkit.prompts as p
        importlib.reload(p)
        return p

    def test_doctor_skill_references_pactkit_doctor(self):
        """SKILL_DOCTOR_MD must reference pactkit doctor CLI."""
        from pactkit.prompts.skills import SKILL_DOCTOR_MD
        assert "pactkit doctor" in SKILL_DOCTOR_MD

    def test_release_skill_references_pactkit_backfill(self):
        """SKILL_RELEASE_MD must reference pactkit backfill-release."""
        from pactkit.prompts.skills import SKILL_RELEASE_MD
        assert "pactkit backfill-release" in SKILL_RELEASE_MD

    def test_done_command_references_pactkit_issue_sync(self):
        """Done command must reference pactkit issue-sync."""
        p = self._reload_prompts()
        done = p.COMMANDS_CONTENT["project-done.md"]
        assert "pactkit issue-sync" in done
