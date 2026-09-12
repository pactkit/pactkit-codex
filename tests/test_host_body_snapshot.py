"""This host's deployed prompt bodies, pinned against a golden (R7/AC10).

2026-09-12 review (83/100, gap 2): the zero-credential acceptance split
left adapter-host body comparison out of CI — the core workflow compares
classic only. This suite pins the CODEX deployment's prompt bodies:

- digest drift (a rule edited or deleted inside a prompt body) fails,
  naming the file;
- a core version mismatch fails with an explicit action — regenerate the
  golden against the new core, or publish the matching core release
  (PENDING-COMPATIBLE-CORE, see the spec R8 release-window semantics);
- a probe test deploys, edits one body in place, and proves the SAME
  comparison logic flags it (删改必被检出, not vacuous).

Regenerate with: tests/scripts/refresh_host_body_golden.py
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

HOST = "codex"
GOLDEN = Path(__file__).parent / "fixtures" / "host_body_golden.json"
DEPLOY_SUFFIXES = (".md", ".json", ".toml")


def _core_version() -> str:
    import importlib.metadata as m

    return m.version("pactkit")


def _normalize(content: str, deploy_root: str) -> str:
    """Strip only the deterministic environment difference: the deploy root
    path baked into rendered prompts. Rule text stays — normalizing it would
    swallow the drift this suite exists to catch."""
    return content.replace(deploy_root, "<DEPLOY_ROOT>")


def _deployed_digests(tmp_path: Path) -> tuple[dict[str, str] | None, subprocess.CompletedProcess]:
    home = tmp_path / "home"
    target = tmp_path / "deploy"
    home.mkdir()
    proc = subprocess.run(
        [sys.executable, "-m", "pactkit", "init", "--format", HOST, "--target", str(target)],
        capture_output=True, text=True, timeout=180,
        env={"PATH": "/usr/bin:/bin", "HOME": str(home), "COLUMNS": "200"},
    )
    if proc.returncode != 0:
        return None, proc
    digests: dict[str, str] = {}
    for path in sorted(target.rglob("*")):
        if not path.is_file() or path.suffix not in DEPLOY_SUFFIXES:
            continue
        body = _normalize(path.read_text(encoding="utf-8"), str(target))
        digests[path.relative_to(target).as_posix()] = hashlib.sha256(
            body.encode("utf-8")
        ).hexdigest()
    return digests, proc


def _assert_no_drift(golden_digests: dict[str, str], live: dict[str, str]) -> None:
    """The one comparison both the golden test and the tamper probe use."""
    changed = sorted(
        k for k in set(golden_digests) & set(live) if golden_digests[k] != live[k]
    )
    removed = sorted(set(golden_digests) - set(live))
    added = sorted(set(live) - set(golden_digests))
    assert not (changed or removed or added), (
        f"prompt body drift: changed={changed} removed={removed} added={added} "
        f"— if the core prompts changed, regenerate the golden "
        f"(tests/scripts/refresh_host_body_golden.py) or publish the matching "
        f"core release first (PENDING-COMPATIBLE-CORE)"
    )


class TestHostBodySnapshot:
    def test_bodies_match_the_golden(self, tmp_path):
        golden = json.loads(GOLDEN.read_text(encoding="utf-8"))
        core_v = _core_version()
        if golden["core_version"] != core_v:
            pytest.fail(
                f"PENDING-COMPATIBLE-CORE: the {HOST} golden was generated "
                f"against core {golden['core_version']}, this environment has "
                f"{core_v}. Either regenerate it after the core change "
                f"(tests/scripts/refresh_host_body_golden.py) or publish the "
                f"matching core release first (spec R8 release-window semantics)."
            )
        live, proc = _deployed_digests(tmp_path)
        assert live is not None, (
            f"{HOST} deploy failed: {proc.stdout[-300:]}{proc.stderr[-300:]}"
        )
        _assert_no_drift(golden["body_digests"], live)

    def test_a_body_edit_is_caught_by_the_same_comparison(self, tmp_path):
        """Non-vacuity, end to end: deploy, edit one prompt body in place,
        and the SAME comparison that guards the golden must flag it."""
        golden = json.loads(GOLDEN.read_text(encoding="utf-8"))
        live, proc = _deployed_digests(tmp_path)
        assert live is not None, f"{HOST} deploy failed: {proc.stderr[-300:]}"
        target = tmp_path / "deploy"
        # Pick a real deployed prompt body and delete one rule line from it.
        victims = sorted(
            p for p in target.rglob("*.md") if p.relative_to(target).as_posix() in golden["body_digests"]
        )
        assert victims, "no deployed .md body found to tamper with"
        victim = victims[0]
        rel = victim.relative_to(target).as_posix()
        body = victim.read_text(encoding="utf-8")
        victim.write_text(body + "\n- deleted in a review\n", encoding="utf-8")

        tampered = {
            p.relative_to(target).as_posix(): hashlib.sha256(
                _normalize(p.read_text(encoding="utf-8"), str(target)).encode("utf-8")
            ).hexdigest()
            for p in sorted(target.rglob("*"))
            if p.is_file() and p.suffix in DEPLOY_SUFFIXES
        }
        with pytest.raises(AssertionError, match=rel):
            _assert_no_drift(golden["body_digests"], tampered)
