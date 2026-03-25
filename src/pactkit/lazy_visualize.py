"""Lazy Visualize — skip graph generation when no source changes (STORY-slim-014 R7).

Implements the Lazy Visualize Protocol from docs/rules/07-shared-protocols.md:
  If source files changed OR code_graph.mmd is missing → visualize.
  Else → skip with log: "Graph up-to-date — no source changes".
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from pactkit.cleaners import detect_stack
from pactkit.prompts.workflows import LANG_PROFILES

# Canonical graph output path (relative to project root)
_GRAPH_PATH = Path("docs") / "architecture" / "graphs" / "code_graph.mmd"


def should_visualize(
    project_root: Path,
    stack: str = "auto",
) -> tuple[bool, str]:
    """Determine whether visualization should run.

    Logic:
    1. Detect stack (reuse cleaners.detect_stack when stack='auto').
    2. Get source_dirs and file_ext from LANG_PROFILES.
    3. Run `git diff --name-only HEAD` to get changed files.
    4. If git fails → (True, "unable to detect changes").
    5. If graph file missing → (True, "code_graph.mmd missing").
    6. If any changed file is under source_dirs with matching extension
       → (True, "source files changed: <files>").
    7. Otherwise → (False, "Graph up-to-date — no source changes").

    Args:
        project_root: Absolute path to the project root directory.
        stack: Language stack or 'auto' to auto-detect.

    Returns:
        (should_run, reason) tuple.
    """
    # Resolve stack
    resolved_stack = stack if stack != "auto" else detect_stack(project_root)
    profile = LANG_PROFILES.get(resolved_stack, LANG_PROFILES["python"])
    source_dirs: list[str] = profile["source_dirs"]
    file_ext: str = profile["file_ext"]

    # Run git diff to get changed files
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD"],
            capture_output=True,
            text=True,
            cwd=str(project_root),
        )
        if result.returncode != 0:
            return (True, "unable to detect changes (git diff failed)")
        changed_files = [f.strip() for f in result.stdout.splitlines() if f.strip()]
    except (subprocess.CalledProcessError, OSError, Exception):
        return (True, "unable to detect changes (git not available)")

    # Check if graph file exists
    graph_file = project_root / _GRAPH_PATH
    graph_exists = graph_file.exists()

    # Find source file changes
    source_changes = [
        f for f in changed_files
        if f.endswith(file_ext) and any(f.startswith(d) for d in source_dirs)
    ]

    if source_changes:
        files_str = ", ".join(source_changes)
        return (True, f"source files changed: {files_str}")

    if not graph_exists:
        return (True, f"code_graph.mmd missing: {graph_file}")

    return (False, "Graph up-to-date — no source changes")


def run_visualize_single(project_root: Path, mode: str) -> None:
    """Execute visualize.py for a single graph mode (HOTFIX-slim-023)."""
    import sys

    viz_script = Path(__file__).resolve().parent / "skills" / "visualize.py"
    if not viz_script.exists():
        print(f"visualize.py not found: {viz_script}")
        return
    subprocess.run(
        [sys.executable, str(viz_script), "visualize", "--mode", mode],
        cwd=str(project_root),
    )


def run_visualize_graphs(project_root: Path) -> None:
    """Execute visualize.py to regenerate all graph files.

    Runs file, class, call modes. Also refreshes focus graphs if they exist.
    """
    import sys

    viz_script = Path(__file__).resolve().parent / "skills" / "visualize.py"
    if not viz_script.exists():
        return

    mode_flag = "--mode"
    for mode in ["file", "class", "call"]:
        subprocess.run([sys.executable, str(viz_script), "visualize", mode_flag, mode],
                       cwd=str(project_root))

    # Refresh focus graphs if they exist
    graph_dir = project_root / "docs" / "architecture" / "graphs"
    if (graph_dir / "focus_file_graph.mmd").exists():
        subprocess.run([sys.executable, str(viz_script), "visualize", "--focus", "cli"],
                       cwd=str(project_root))
    if (graph_dir / "focus_call_graph.mmd").exists():
        subprocess.run([sys.executable, str(viz_script), "visualize", "--focus", "cli", mode_flag, "call"],
                       cwd=str(project_root))
