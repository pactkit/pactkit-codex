"""GitHub issue lifecycle sync — deterministic issue management (STORY-slim-015 R5).

Replaces prompt-based issue tracker verification from Done Phase 3.5.5/3.6.
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path


def _parse_item_type(item_id: str) -> str:
    """Extract item type prefix (STORY, BUG, HOTFIX)."""
    if item_id.startswith("STORY"):
        return "STORY"
    elif item_id.startswith("BUG"):
        return "BUG"
    elif item_id.startswith("HOTFIX"):
        return "HOTFIX"
    return "UNKNOWN"


def _get_issue_tracker_provider(project_root: Path) -> str | None:
    """Read issue_tracker.provider from pactkit.yaml."""
    import yaml

    from pactkit.config import find_pactkit_yaml

    yaml_path = find_pactkit_yaml(project_root)
    if yaml_path is None:
        return None

    try:
        with open(yaml_path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    except Exception:
        return None

    tracker = data.get("issue_tracker", {})
    if not isinstance(tracker, dict):
        return None
    return tracker.get("provider")


def _check_gh_available() -> bool:
    """Check if gh CLI is available."""
    try:
        subprocess.run(
            ["gh", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def _search_issue(item_id: str) -> dict | None:
    """Search for existing GitHub issue by item ID."""
    try:
        result = subprocess.run(
            ["gh", "issue", "list", "--search", item_id,
             "--state", "all", "--json", "number,title,url"],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode != 0:
            return None
        issues = json.loads(result.stdout)
        for issue in issues:
            title = issue.get("title", "")
            if re.search(rf"(?<!\w){re.escape(item_id)}(?!\w)", title):
                return issue
        return None
    except Exception:
        return None


def _create_issue(item_id: str, title: str = "") -> dict | None:
    """Create a GitHub issue for the item."""
    full_title = f"{item_id}: {title}" if title else item_id
    body = f"Spec: docs/specs/{item_id}.md\n\n**Status**: Backfilled during Done phase"
    try:
        result = subprocess.run(
            ["gh", "issue", "create", "--title", full_title, "--body", body],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode != 0:
            return None
        # Parse URL from output
        url = result.stdout.strip()
        # Extract number from URL
        number = url.rstrip("/").rsplit("/", 1)[-1]
        return {"number": number, "url": url}
    except Exception:
        return None


def _close_issue(number: str, commit_sha: str = "") -> bool:
    """Close a GitHub issue."""
    cmd = ["gh", "issue", "close", number]
    if commit_sha:
        cmd += ["--comment", f"Completed in {commit_sha}"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return result.returncode == 0
    except Exception:
        return False


def issue_sync(item_id: str, project_root: Path) -> dict:
    """Sync GitHub issue for the given item.

    Returns:
        {"action": "skipped"|"created"|"found"|"error", "message": ..., ...}
    """
    item_type = _parse_item_type(item_id)

    # STORY items are skipped for IP protection
    if item_type == "STORY":
        return {"action": "skipped", "message": "Issue sync skipped for STORY (IP protection)"}

    # Check provider config
    provider = _get_issue_tracker_provider(project_root)
    if provider is None or provider == "none":
        return {"action": "skipped", "message": "Issue tracker not configured or provider is none"}

    if provider != "github":
        return {"action": "skipped", "message": f"Unsupported provider: {provider}"}

    # Check gh CLI
    if not _check_gh_available():
        return {"action": "error", "message": "gh CLI unavailable"}

    # Search for existing issue
    existing = _search_issue(item_id)
    if existing:
        return {
            "action": "found",
            "message": f"Found existing issue #{existing['number']}",
            "number": existing["number"],
            "url": existing.get("url", ""),
        }

    # Create new issue
    created = _create_issue(item_id)
    if created:
        return {
            "action": "created",
            "message": f"Created issue #{created['number']}",
            "number": created["number"],
            "url": created.get("url", ""),
        }

    return {"action": "error", "message": "Failed to create GitHub issue"}
