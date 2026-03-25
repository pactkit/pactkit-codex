"""Init guard — deterministic project readiness check (STORY-slim-014 R1).

Replaces the prompt-based Init Guard from Plan Phase 0.5.
"""
from __future__ import annotations

from pathlib import Path

from pactkit import __version__
from pactkit.config import find_pactkit_yaml, load_config


def check_init_markers(project_root: Path) -> tuple[bool, list[str]]:
    """Check whether the project has been initialized with PactKit.

    Checks 3 markers:
        1. pactkit.yaml exists (via find_pactkit_yaml)
        2. docs/product/sprint_board.md exists
        3. docs/architecture/graphs/ directory exists

    Returns:
        (ok, missing) — True if all present, list of missing marker descriptions.
    """
    missing: list[str] = []

    # 1. pactkit.yaml
    if find_pactkit_yaml(project_root) is None:
        missing.append("pactkit.yaml not found (run `pactkit init`)")

    # 2. Sprint board
    board = project_root / "docs" / "product" / "sprint_board.md"
    if not board.exists():
        missing.append("docs/product/sprint_board.md not found (run `/project-init`)")

    # 3. Architecture graphs dir
    graphs = project_root / "docs" / "architecture" / "graphs"
    if not graphs.is_dir():
        missing.append("docs/architecture/graphs/ not found (run `/project-init`)")

    return (len(missing) == 0, missing)


# Expected top-level keys in pactkit.yaml
_EXPECTED_CONFIG_KEYS = ("developer", "stack", "agents", "commands", "skills", "rules")


def check_config_completeness(project_root: Path) -> list[str]:
    """Check pactkit.yaml for expected top-level sections.

    Returns:
        List of warning strings; empty list means config is complete.
    """
    yaml_path = find_pactkit_yaml(project_root)
    if yaml_path is None:
        return ["pactkit.yaml not found — skipping config completeness check"]

    try:
        import yaml
        with open(yaml_path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    except Exception:
        return [f"Cannot parse {yaml_path}"]

    warnings: list[str] = []
    for key in _EXPECTED_CONFIG_KEYS:
        if key not in data:
            warnings.append(f"Missing config section: '{key}' in {yaml_path.name}")
    return warnings


def check_version_mismatch(project_root: Path) -> str | None:
    """Check if pactkit.yaml version differs from installed __version__.

    Returns:
        Warning message if mismatch, None if versions match or yaml not found.
    """
    yaml_path = find_pactkit_yaml(project_root)
    if yaml_path is None:
        return None

    cfg = load_config(yaml_path)
    yaml_version = cfg.get("version", "")
    if yaml_version and yaml_version != __version__:
        return f"Version mismatch: pactkit.yaml {yaml_version} vs installed {__version__}"
    return None
