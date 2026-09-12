#!/usr/bin/env python3
"""Regenerate tests/fixtures/host_body_golden.json for THIS adapter host.

Run from the adapter repo root in the environment whose pactkit you want to
pin (local dev: the workspace core with the pending release content). The
golden records the core version it was generated against — the test fails
with PENDING-COMPATIBLE-CORE when run against any other core version.

Usage: python3 tests/scripts/refresh_host_body_golden.py
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HOST = "codex"
REPO = Path(__file__).resolve().parent.parent.parent
GOLDEN = REPO / "tests" / "fixtures" / "host_body_golden.json"
DEPLOY_SUFFIXES = (".md", ".json", ".toml")


def main() -> int:
    import importlib.metadata as m

    core_version = m.version("pactkit")
    with tempfile.TemporaryDirectory() as tmp:
        home = Path(tmp) / "home"
        target = Path(tmp) / "deploy"
        home.mkdir()
        proc = subprocess.run(
            [sys.executable, "-m", "pactkit", "init", "--format", HOST,
             "--target", str(target)],
            capture_output=True, text=True, timeout=180,
            env={"PATH": "/usr/bin:/bin", "HOME": str(home), "COLUMNS": "200"},
        )
        if proc.returncode != 0:
            print(proc.stdout[-500:])
            print(proc.stderr[-500:])
            return 1
        digests: dict[str, str] = {}
        for path in sorted(target.rglob("*")):
            if not path.is_file() or path.suffix not in DEPLOY_SUFFIXES:
                continue
            body = path.read_text(encoding="utf-8").replace(str(target), "<DEPLOY_ROOT>")
            digests[path.relative_to(target).as_posix()] = hashlib.sha256(
                body.encode("utf-8")
            ).hexdigest()
    GOLDEN.parent.mkdir(parents=True, exist_ok=True)
    GOLDEN.write_text(
        json.dumps(
            {"host": HOST, "core_version": core_version, "body_digests": digests},
            indent=2, ensure_ascii=False, sort_keys=True,
        ) + "\n",
        encoding="utf-8",
    )
    print(f"pinned {len(digests)} bodies for {HOST} against core {core_version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
