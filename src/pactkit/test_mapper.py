"""Source-to-test file mapping — deterministic test discovery (STORY-slim-016 R1).

Replaces the prompt-based Test Mapping Protocol referenced in Act/Check/Done/Hotfix.
"""
from __future__ import annotations

from pathlib import Path

from pactkit.cleaners import detect_stack
from pactkit.prompts.workflows import LANG_PROFILES


def map_to_tests(
    changed_files: list[str],
    project_root: Path,
) -> dict:
    """Map changed source files to corresponding test files.

    Returns:
        {"mapped": [str], "reason": str}
    """
    stack = detect_stack(project_root)
    profile = LANG_PROFILES.get(stack)
    if not profile or "test_map_pattern" not in profile:
        return {"mapped": [], "reason": f"No test_map_pattern for stack '{stack}'"}

    pattern = profile["test_map_pattern"]
    source_dirs = profile.get("source_dirs", [])
    file_ext = profile.get("file_ext", "")

    mapped: list[str] = []

    for fpath in changed_files:
        p = Path(fpath)

        # Skip non-source files
        if file_ext and p.suffix != file_ext:
            continue

        # Extract module name (stem without extension)
        module = p.stem

        # Build test path from pattern
        test_path_str = pattern.replace("{module}", module)

        # Handle {package} placeholder (Java/Go)
        if "{package}" in test_path_str:
            # Extract package path from source file
            for sd in source_dirs:
                if fpath.startswith(sd):
                    rel = fpath[len(sd):]
                    package = str(Path(rel).parent)
                    test_path_str = test_path_str.replace("{package}", package)
                    break

        test_path = project_root / test_path_str
        if test_path.exists() and str(test_path_str) not in mapped:
            mapped.append(str(test_path_str))

    return {"mapped": mapped, "reason": "" if mapped else "No matching test files found"}
