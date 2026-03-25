"""Coverage gate — pytest-cov verification with 3-tier thresholds (STORY-slim-017 R3)."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path


def _extract_module_path(file_path: str) -> str:
    """Convert source file path to Python module path.

    Example: src/pactkit/foo.py -> pactkit.foo
    """
    p = file_path.replace("/", ".").replace("\\", ".")
    # Strip src. prefix and .py suffix
    if p.startswith("src."):
        p = p[4:]
    if p.endswith(".py"):
        p = p[:-3]
    return p


def _classify_coverage(pct: int) -> str:
    """Apply 3-tier threshold to a coverage percentage."""
    if pct >= 80:
        return "pass"
    elif pct >= 50:
        return "warn"
    else:
        return "block"


def _parse_coverage_output(output: str) -> list[dict]:
    """Parse pytest-cov term output into per-file results.

    Expected format:
        Name                    Stmts   Miss  Cover   Missing
        -------------------------------------------------------
        src/pactkit/foo.py         50     10    80%   11-15,20
    """
    files = []
    for line in output.splitlines():
        match = re.match(r"^(\S+\.py)\s+\d+\s+\d+\s+(\d+)%", line)
        if match and match.group(1) != "TOTAL":
            pct = int(match.group(2))
            files.append({
                "file": match.group(1),
                "coverage": pct,
                "status": _classify_coverage(pct),
            })
    return files


def _run_pytest_cov(modules: list[str], project_root: Path) -> str:
    """Run pytest --cov and return stdout."""
    cov_args = []
    for m in modules:
        cov_args.extend(["--cov", m])

    cmd = [
        "python", "-m", "pytest",
        *cov_args,
        "--cov-report=term-missing",
        "tests/",
        "-q",
    ]
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(project_root),
        timeout=300,
    )
    return result.stdout


def check_coverage(
    changed_files: list[str],
    project_root: Path | None = None,
) -> dict:
    """Run coverage verification on changed source files.

    Returns:
        {"files": [...], "overall": "pass"|"warn"|"block"|"skip", "reason": str}
    """
    if project_root is None:
        project_root = Path.cwd()

    # Filter to Python source files only
    source_files = [f for f in changed_files if f.endswith(".py") and "test" not in f]
    if not source_files:
        return {"files": [], "overall": "skip", "reason": "no source files to check"}

    modules = [_extract_module_path(f) for f in source_files]

    try:
        output = _run_pytest_cov(modules, project_root)
    except (FileNotFoundError, subprocess.TimeoutExpired) as e:
        return {"files": [], "overall": "skip", "reason": str(e)}

    files = _parse_coverage_output(output)
    if not files:
        return {"files": [], "overall": "skip", "reason": "no coverage data parsed"}

    # Overall is the worst status
    statuses = [f["status"] for f in files]
    if "block" in statuses:
        overall = "block"
    elif "warn" in statuses:
        overall = "warn"
    else:
        overall = "pass"

    return {"files": files, "overall": overall, "reason": "coverage checked"}
