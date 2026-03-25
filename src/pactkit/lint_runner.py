"""Stack-aware lint runner — deterministic lint gate (STORY-slim-016 R2).

Replaces the prompt-based Smart Lint Gate from Done Phase 2.5 Step 2.7.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

from pactkit.cleaners import detect_stack
from pactkit.prompts.workflows import LANG_PROFILES


def run_lint(
    project_root: Path,
    fix: bool = False,
) -> dict:
    """Run stack-aware lint command.

    Returns:
        {"exit_code": int, "stdout": str, "blocking": bool, "message": str}
    """
    stack = detect_stack(project_root)
    profile = LANG_PROFILES.get(stack)

    if not profile or "lint_command" not in profile:
        return {
            "exit_code": 0,
            "stdout": "",
            "blocking": False,
            "message": f"No lint command configured for stack '{stack}' — skipping",
        }

    lint_cmd = profile["lint_command"]

    # Read config for auto_fix and lint_blocking
    auto_fix = False
    lint_blocking = False
    try:
        from pactkit.config import find_pactkit_yaml, load_config

        yaml_path = find_pactkit_yaml(project_root)
        cfg = load_config(yaml_path) if yaml_path else {}
        auto_fix = cfg.get("auto_fix", False)
        lint_blocking = cfg.get("lint_blocking", False)
    except Exception:
        pass

    should_fix = fix or auto_fix

    # Run fix pass first if requested
    if should_fix:
        fix_cmd = _add_fix_flag(lint_cmd, stack)
        subprocess.run(
            fix_cmd,
            shell=True,
            cwd=str(project_root),
            capture_output=True,
            text=True,
            timeout=120,
        )

    # Run check pass
    result = subprocess.run(
        lint_cmd,
        shell=True,
        cwd=str(project_root),
        capture_output=True,
        text=True,
        timeout=120,
    )

    return {
        "exit_code": result.returncode,
        "stdout": result.stdout + result.stderr,
        "blocking": lint_blocking,
        "message": "Lint passed" if result.returncode == 0 else "Lint errors found",
    }


def _add_fix_flag(lint_cmd: str, stack: str) -> str:
    """Add the fix flag to a lint command based on stack."""
    # Stack-specific fix flag insertion
    if stack == "python" and "ruff check" in lint_cmd:
        return lint_cmd.replace("ruff check", "ruff check --fix", 1)
    elif stack == "node" and "eslint" in lint_cmd:
        return lint_cmd + " --fix"
    elif stack == "go" and "golangci-lint" in lint_cmd:
        return lint_cmd + " --fix"
    # Default: append --fix
    return lint_cmd + " --fix"
