"""Project health diagnostics — deterministic doctor checks (STORY-slim-015 R1-R3).

Replaces prompt-based diagnostics from SKILL_DOCTOR_MD.
"""
from __future__ import annotations

import re
from pathlib import Path

# Pattern to extract item IDs from filenames and board text
_ITEM_ID_RE = re.compile(r"((?:STORY|BUG|HOTFIX)(?:-[\w]+)?-\d+)")


def check_orphaned_specs(project_root: Path) -> dict:
    """Cross-reference specs dir vs board + archive.

    Returns:
        {"orphaned": [{"id": ...}], "missing": [{"id": ...}]}
    """
    specs_dir = project_root / "docs" / "specs"
    board_path = project_root / "docs" / "product" / "sprint_board.md"
    archive_dir = project_root / "docs" / "product" / "archive"

    # Collect spec IDs from filenames
    spec_ids: set[str] = set()
    if specs_dir.is_dir():
        for f in specs_dir.iterdir():
            if f.suffix == ".md":
                m = _ITEM_ID_RE.match(f.stem)
                if m:
                    spec_ids.add(m.group(1))

    # Collect board IDs
    board_ids: set[str] = set()
    if board_path.exists():
        board_text = board_path.read_text(encoding="utf-8")
        board_ids.update(_ITEM_ID_RE.findall(board_text))

    # Collect archive IDs
    archive_ids: set[str] = set()
    if archive_dir.is_dir():
        for f in archive_dir.iterdir():
            if f.suffix == ".md":
                archive_ids.update(_ITEM_ID_RE.findall(f.read_text(encoding="utf-8")))

    all_referenced = board_ids | archive_ids

    orphaned = [{"id": sid} for sid in sorted(spec_ids - all_referenced)]
    missing = [{"id": bid} for bid in sorted(all_referenced - spec_ids)
               if _ITEM_ID_RE.match(bid)]

    return {"orphaned": orphaned, "missing": missing}


def check_config_drift(project_root: Path) -> dict:
    """Compare pactkit.yaml declared items vs deployed files.

    Returns:
        {"missing_deployments": [{"type": ..., "name": ...}]}
    """
    import yaml

    from pactkit.config import find_pactkit_yaml

    yaml_path = find_pactkit_yaml(project_root)
    if yaml_path is None:
        return {"missing_deployments": [], "error": "pactkit.yaml not found"}

    with open(yaml_path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    config_dir = yaml_path.parent  # .claude/ or .opencode/
    missing: list[dict] = []

    # Check agents
    for agent in data.get("agents", []):
        agent_file = config_dir / "agents" / f"{agent}.md"
        if not agent_file.exists():
            missing.append({"type": "agent", "name": agent})

    # Check commands
    for cmd in data.get("commands", []):
        cmd_file = config_dir / "commands" / f"{cmd}.md"
        if not cmd_file.exists():
            missing.append({"type": "command", "name": cmd})

    # Check skills
    for skill in data.get("skills", []):
        skill_dir = config_dir / "skills" / skill
        skill_file = config_dir / "skills" / f"{skill}.md"
        if not skill_dir.is_dir() and not skill_file.exists():
            missing.append({"type": "skill", "name": skill})

    # Check rules
    for rule in data.get("rules", []):
        rule_file = config_dir / "rules" / f"{rule}.md"
        if not rule_file.exists():
            missing.append({"type": "rule", "name": rule})

    return {"missing_deployments": missing}


def check_stale_graphs(
    project_root: Path,
    threshold_days: int = 7,
) -> dict:
    """Compare graph mtimes vs newest source file.

    Returns:
        {"stale": [{"file": ..., "days_behind": ...}], "missing": bool}
    """
    graph_dir = project_root / "docs" / "architecture" / "graphs"

    if not graph_dir.is_dir():
        return {"stale": [], "missing": True}

    # Find newest source file mtime
    source_dirs = ["src/"]  # Default Python
    try:
        from pactkit.config import load_config
        from pactkit.prompts.workflows import LANG_PROFILES

        cfg = load_config(project_root)
        stack = cfg.get("stack", "python")
        profile = LANG_PROFILES.get(stack, LANG_PROFILES.get("python", {}))
        source_dirs = profile.get("source_dirs", ["src/"])
    except Exception:
        pass

    newest_source_mtime = 0.0
    for sd in source_dirs:
        src_path = project_root / sd
        if src_path.is_dir():
            for f in src_path.rglob("*"):
                if f.is_file() and not f.name.startswith("."):
                    newest_source_mtime = max(newest_source_mtime, f.stat().st_mtime)

    if newest_source_mtime == 0.0:
        return {"stale": [], "missing": False}

    threshold_seconds = threshold_days * 86400
    stale: list[dict] = []

    for graph in graph_dir.glob("*.mmd"):
        graph_mtime = graph.stat().st_mtime
        age_diff = newest_source_mtime - graph_mtime
        if age_diff > threshold_seconds:
            days_behind = int(age_diff / 86400)
            stale.append({"file": graph.name, "days_behind": days_behind})

    return {"stale": stale, "missing": False}


def check_hld_module_count(project_root: Path) -> dict:
    """Compare module count in system_design.mmd vs actual source files.

    Returns:
        {"source_modules": N, "hld_nodes": M, "drift": N - M}
    """
    hld_path = project_root / "docs" / "architecture" / "graphs" / "system_design.mmd"

    # Count actual .py modules (excluding __init__.py, __pycache__)
    src_dir = project_root / "src" / "pactkit"
    source_modules = 0
    if src_dir.is_dir():
        for f in src_dir.iterdir():
            if (f.suffix == ".py"
                    and f.name != "__init__.py"
                    and not f.name.startswith("__")):
                source_modules += 1

    # Count node declarations in system_design.mmd
    hld_nodes = 0
    if hld_path.exists():
        hld_text = hld_path.read_text(encoding="utf-8")
        # Count Mermaid node declarations: Identifier["label"]
        hld_nodes = len(re.findall(r'\w+\["[^"]+"\]', hld_text))

    return {
        "source_modules": source_modules,
        "hld_nodes": hld_nodes,
        "drift": source_modules - hld_nodes,
    }
