"""Security scope auto-detection — R6 (STORY-slim-014).

Detects which SEC-1 through SEC-8 security checks apply based on
file paths and, optionally, file content.
"""

from __future__ import annotations

import re
from pathlib import Path, PurePosixPath

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _is_docs_or_tests_only(file_paths: list[str]) -> bool:
    """Return True if ALL files are docs, tests, markdown, or README files."""
    for fp in file_paths:
        p = PurePosixPath(fp)
        parts = p.parts
        # Check common prefix markers
        if parts and parts[0] in ("docs", "tests"):
            continue
        if fp.endswith(".md"):
            continue
        if p.name.startswith("README"):
            continue
        return False
    return True


def _read_content(file_path: str, project_root: Path | None) -> str | None:
    """Return file content if project_root is provided and file exists; else None."""
    if project_root is None:
        return None
    full = project_root / file_path
    try:
        return full.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


def _path_matches_any(fp: str, fragments: tuple[str, ...]) -> bool:
    """Return True if the file path contains any of the given path fragments."""
    p = PurePosixPath(fp)
    fp_str = fp.replace("\\", "/")
    for frag in fragments:
        if frag in fp_str:
            return True
        # Also check by parts prefix (e.g. 'api/' matches parts[0]=='api')
        for part in p.parts[:-1]:
            if part == frag.rstrip("/"):
                return True
    return False


def _path_ends_with_ext(fp: str, exts: tuple[str, ...]) -> bool:
    """Return True if the file has one of the given extensions."""
    return any(fp.endswith(ext) for ext in exts)


# ---------------------------------------------------------------------------
# Content pattern helpers
# ---------------------------------------------------------------------------

_SEC2_CONTENT_PATTERNS = re.compile(
    r"request\.|form\.|input|argv|sys\.stdin|process\.argv"
)
_SEC3_CONTENT_PATTERNS = re.compile(
    r"\bSELECT\b|\bINSERT\b|\bUPDATE\b|\bDELETE\b|\.query\(|\.filter\(|\.objects\."
)
_SEC4_CONTENT_PATTERNS = re.compile(
    r"innerHTML|dangerouslySetInnerHTML"
)
_SEC5_CONTENT_PATTERNS = re.compile(
    r"\btoken\b|\bjwt\b|\bcookie\b|\bsession\b"
)
_SEC7_CONTENT_PATTERNS = re.compile(
    r"except\b|catch\s*\(|rescue\b|\.catch\("
)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def detect_security_scope(
    file_paths: list[str],
    project_root: Path | None = None,
) -> list[dict]:
    """Detect which SEC-1 through SEC-8 checks apply.

    Args:
        file_paths: List of relative file paths that were changed.
        project_root: Optional project root; if provided, content sniffing
            is performed for SEC-2 through SEC-7.

    Returns:
        List of 8 dicts: [{"check": "SEC-1", "applicable": bool, "reason": str}]
    """
    # Docs/tests-only shortcut: all checks N/A
    if _is_docs_or_tests_only(file_paths):
        return [
            {"check": f"SEC-{i}", "applicable": False, "reason": "docs/tests only"}
            for i in range(1, 9)
        ]

    results = []

    # Precompute contents for content sniffing (only if project_root given)
    contents: dict[str, str] = {}
    if project_root is not None:
        for fp in file_paths:
            c = _read_content(fp, project_root)
            if c is not None:
                contents[fp] = c

    def _any_content_matches(pattern: re.Pattern) -> bool:
        return any(pattern.search(c) for c in contents.values())

    # SEC-1: Any .py, .js, .ts, .go, .java file
    sec1_exts = (".py", ".js", ".ts", ".go", ".java")
    sec1_applicable = any(_path_ends_with_ext(fp, sec1_exts) for fp in file_paths)
    results.append({
        "check": "SEC-1",
        "applicable": sec1_applicable,
        "reason": "source code file detected" if sec1_applicable else "no source code files",
    })

    # SEC-2: Input handling — path or content patterns
    sec2_path_applicable = any(
        _path_ends_with_ext(fp, sec1_exts) and (
            "input" in fp or "handler" in fp or "form" in fp
        )
        for fp in file_paths
    )
    sec2_content_applicable = _any_content_matches(_SEC2_CONTENT_PATTERNS)
    sec2_applicable = sec2_path_applicable or sec2_content_applicable
    if sec2_applicable:
        reason = "input handling patterns detected"
    else:
        reason = "no input handling patterns"
    results.append({"check": "SEC-2", "applicable": sec2_applicable, "reason": reason})

    # SEC-3: SQL/ORM — path matches models/, dao/, repository/ or content
    sec3_path_frags = ("models/", "dao/", "repository/")
    sec3_path_applicable = any(_path_matches_any(fp, sec3_path_frags) for fp in file_paths)
    sec3_content_applicable = _any_content_matches(_SEC3_CONTENT_PATTERNS)
    sec3_applicable = sec3_path_applicable or sec3_content_applicable
    results.append({
        "check": "SEC-3",
        "applicable": sec3_applicable,
        "reason": "database/ORM patterns detected" if sec3_applicable else "no database patterns",
    })

    # SEC-4: XSS — path matches .tsx, .vue, .svelte, .html or content
    sec4_exts = (".tsx", ".vue", ".svelte", ".html")
    sec4_path_applicable = any(_path_ends_with_ext(fp, sec4_exts) for fp in file_paths)
    sec4_content_applicable = _any_content_matches(_SEC4_CONTENT_PATTERNS)
    sec4_applicable = sec4_path_applicable or sec4_content_applicable
    results.append({
        "check": "SEC-4",
        "applicable": sec4_applicable,
        "reason": "frontend/template files detected" if sec4_applicable else "no frontend files",
    })

    # SEC-5: Auth/Session — path or content
    sec5_path_frags = ("auth/", "session/", "login/")
    sec5_path_applicable = any(_path_matches_any(fp, sec5_path_frags) for fp in file_paths)
    sec5_content_applicable = _any_content_matches(_SEC5_CONTENT_PATTERNS)
    sec5_applicable = sec5_path_applicable or sec5_content_applicable
    results.append({
        "check": "SEC-5",
        "applicable": sec5_applicable,
        "reason": "auth/session patterns detected" if sec5_applicable else "no auth patterns",
    })

    # SEC-6: Access control — path matches api/, routes/, endpoints/, controllers/
    sec6_path_frags = ("api/", "routes/", "endpoints/", "controllers/")
    sec6_applicable = any(_path_matches_any(fp, sec6_path_frags) for fp in file_paths)
    results.append({
        "check": "SEC-6",
        "applicable": sec6_applicable,
        "reason": "API/route files detected" if sec6_applicable else "no API/route files",
    })

    # SEC-7: Error handling — path matches api/, routes/ or content exception patterns
    sec7_path_frags = ("api/", "routes/")
    sec7_path_applicable = any(_path_matches_any(fp, sec7_path_frags) for fp in file_paths)
    sec7_content_applicable = _any_content_matches(_SEC7_CONTENT_PATTERNS)
    sec7_applicable = sec7_path_applicable or sec7_content_applicable
    results.append({
        "check": "SEC-7",
        "applicable": sec7_applicable,
        "reason": "error handling patterns detected" if sec7_applicable else "no error handling patterns",
    })

    # SEC-8: Dependency files
    sec8_names = {"package.json", "requirements.txt", "pyproject.toml", "go.mod", "Cargo.toml"}
    sec8_applicable = any(Path(fp).name in sec8_names for fp in file_paths)
    results.append({
        "check": "SEC-8",
        "applicable": sec8_applicable,
        "reason": "dependency manifest detected" if sec8_applicable else "no dependency manifests",
    })

    return results


def format_markdown_table(results: list[dict]) -> str:
    """Render the security scope results as a Markdown table.

    Args:
        results: Output from detect_security_scope().

    Returns:
        Multi-line Markdown table string.
    """
    header = "| Check | Applicable | Reason |"
    separator = "|-------|------------|--------|"
    rows = [
        f"| {r['check']} | {'Yes' if r['applicable'] else 'No'} | {r['reason']} |"
        for r in results
    ]
    return "\n".join([header, separator] + rows)
