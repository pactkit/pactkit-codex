"""Advisory-only Codex Stop hook.

Core WorkUnits own workflow state. This legacy hook may record a sanitized
observation, but it never blocks a turn or schedules continuation work.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pactkit.continuation import ContinuationEngine, ContinuationError
from pactkit.utils import atomic_write

HOOK_PROTOCOL_VERSION = 1
HOOK_STATE_FILE = "pactkit-hook-state.json"
HOOK_TRACE_FILE = "pactkit-hook-observations.jsonl"


def _reference(value: object) -> str | None:
    if not isinstance(value, str) or not value:
        return None
    return "sha256:" + hashlib.sha256(value.encode()).hexdigest()


def _record_observation(
    event: dict[str, Any], *, resolved: dict[str, Any] | None,
    decision: str, reason_code: str, attempt: int | None, duration_ms: int,
) -> None:
    root = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
    path = root / HOOK_STATE_FILE
    script_path = root / "hooks" / "pactkit_stop.py"
    hook_sha256 = (
        hashlib.sha256(script_path.read_bytes()).hexdigest()
        if script_path.is_file() else None
    )
    prior: dict[str, Any] = {}
    if path.is_file():
        try:
            candidate = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(candidate, dict):
                prior = candidate
        except (OSError, json.JSONDecodeError):
            prior = {}
    run_id = resolved.get("run_id") if resolved else None
    runs = prior.get("runs", {})
    if not isinstance(runs, dict):
        runs = {}
    if isinstance(run_id, str):
        run_state = runs.get(run_id, {})
        if not isinstance(run_state, dict):
            run_state = {}
        runs[run_id] = {
            "advisory_observed": bool(run_state.get("advisory_observed")) or decision == "advisory",
        }
    record = {
        "observed": True,
        "validation_mode": os.environ.get("PACTKIT_CODEX_HOOK_VALIDATION_MODE", "host"),
        "hook_protocol_version": HOOK_PROTOCOL_VERSION,
        "hook_sha256": hook_sha256,
        "runs": runs,
        "session_ref": _reference(event.get("session_id")),
        "turn_ref": _reference(event.get("turn_id")),
        "run_id": run_id,
        "workflow_id": resolved.get("workflow_id") if resolved else None,
        "step_id": resolved.get("step_id") if resolved else None,
        "decision": decision,
        "reason_code": reason_code,
        "attempt": attempt,
        "duration_ms": duration_ms,
        "observed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    atomic_write(path, json.dumps(record, indent=2, ensure_ascii=False) + "\n")
    trace_path = root / HOOK_TRACE_FILE
    trace_path.parent.mkdir(parents=True, exist_ok=True)
    with trace_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    _refresh_deploy_manifest(root)


def _refresh_deploy_manifest(root: Path) -> None:
    """Keep the deployed capability projection aligned with live evidence."""
    manifest_path = root / ".pactkit-deployed.json"
    if not manifest_path.is_file():
        return
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            return
        from pactkit_codex.deployer import CodexDeployer

        payload["workflow_continuation"] = CodexDeployer.continuation_capabilities(root)
        atomic_write(
            manifest_path, json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        )
    except (OSError, json.JSONDecodeError, ImportError):
        # The primary decision was already emitted; diagnostics must never
        # turn a valid Stop response into a host-level hook failure.
        return


def handle_stop(event: dict[str, Any]) -> dict[str, Any]:
    """Record advisory Stop evidence and always let the host complete."""
    started = time.monotonic()
    if not isinstance(event, dict) or event.get("hook_event_name") != "Stop":
        if isinstance(event, dict):
            _record_observation(event, resolved=None, decision="advisory",
                                reason_code="invalid_event", attempt=None,
                                duration_ms=int((time.monotonic() - started) * 1000))
        return {}
    cwd, session_id, turn_id = event.get("cwd"), event.get("session_id"), event.get("turn_id")
    if not isinstance(cwd, str) or not isinstance(session_id, str):
        _record_observation(event, resolved=None, decision="advisory",
                            reason_code="invalid_input", attempt=None,
                            duration_ms=int((time.monotonic() - started) * 1000))
        return {}
    root = Path(cwd).expanduser().resolve()
    if not root.is_dir():
        _record_observation(event, resolved=None, decision="advisory",
                            reason_code="invalid_cwd", attempt=None,
                            duration_ms=int((time.monotonic() - started) * 1000))
        return {}
    try:
        resolved = ContinuationEngine(root).resolve_host_run(
            session_id=session_id, turn_id=turn_id if isinstance(turn_id, str) else None,
        )
        reason_code = "active_run"
    except ContinuationError as exc:
        resolved = None
        message = str(exc)
        reason_code = (
            "no_active_run" if message == "no active workflow run"
            else "multiple_active_runs"
            if message == "multiple active workflow runs" else "invalid_state"
        )
    _record_observation(event, resolved=resolved, decision="advisory",
                        reason_code=reason_code, attempt=None,
                        duration_ms=int((time.monotonic() - started) * 1000))
    return {}


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except (json.JSONDecodeError, OSError):
        result = {}
    else:
        result = handle_stop(event)
    json.dump(result, sys.stdout, ensure_ascii=False)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
