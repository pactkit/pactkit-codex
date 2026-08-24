"""Runnable Codex App Server entry point for one Core-issued WorkUnit."""

from __future__ import annotations

import argparse
import json
import re
import sys
from contextlib import redirect_stdout
from dataclasses import asdict, replace
from pathlib import Path
from typing import Any, Callable

from pactkit.utils import atomic_write
from pactkit.workflow_engine import EvidenceReceipt, WorkflowEngine, WorkUnitError

from pactkit_codex.app_server import AppServerError, CodexAppServer
from pactkit_codex.work_unit_adapter import CodexWorkUnitAdapter

AdapterFactory = Callable[[Path, str], CodexWorkUnitAdapter]
_RECEIPT_TEMPLATE_FIELDS = frozenset({
    "claims", "evidence_files", "result_refs", "session_ref",
})
_RECEIPT_TEMPLATE_ERROR = "receipt_template_unavailable"
_RUN_ID = re.compile(r"run-[0-9a-f]{32}")


def _receipt_template(raw: str) -> dict[str, Any]:
    if raw.startswith("@"):
        try:
            raw = Path(raw[1:]).read_text(encoding="utf-8")
        except OSError as exc:
            # Receipt paths are user input and must never escape through a
            # runner error or persisted Attempt.
            raise ValueError(_RECEIPT_TEMPLATE_ERROR) from exc
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError("receipt_template_invalid_json") from exc
    if not isinstance(payload, dict) or set(payload) - _RECEIPT_TEMPLATE_FIELDS:
        raise ValueError("receipt_template_invalid_fields")
    if not isinstance(payload.get("claims", {}), dict):
        raise ValueError("receipt_template_claims_must_be_object")
    if not isinstance(payload.get("evidence_files", []), list) or not all(
        isinstance(path, str) and path for path in payload.get("evidence_files", [])
    ):
        raise ValueError("receipt_template_evidence_files_must_be_list")
    if not isinstance(payload.get("result_refs", []), list) or not all(
        isinstance(reference, str) and reference
        for reference in payload.get("result_refs", [])
    ):
        raise ValueError("receipt_template_result_refs_must_be_list")
    if "session_ref" in payload and (
        not isinstance(payload["session_ref"], str) or not payload["session_ref"]
    ):
        raise ValueError("receipt_template_session_ref_must_be_string")
    return payload


def _receipt_from_template(
    template: dict[str, Any], unit, *, owner: str, root: Path,
) -> EvidenceReceipt:
    """Bind a template to the leased Unit and derive candidate fingerprints.

    ``evidence_files`` is intentionally only a candidate list: Core validates
    both its write scope and the reread fingerprint during submission.
    """
    receipt = EvidenceReceipt.for_files(
        unit,
        owner=owner,
        root=root,
        files=template.get("evidence_files", []),
        claims=dict(template.get("claims", {})),
    )
    return replace(
        receipt,
        result_refs=tuple(template.get("result_refs", [])),
        session_ref=template.get("session_ref"),
    )


def _default_adapter(root: Path, owner: str) -> CodexWorkUnitAdapter:
    return CodexWorkUnitAdapter(
        WorkflowEngine(root), CodexAppServer(cwd=root), owner=owner,
    )


def _session_path(root: Path, run_id: str) -> Path:
    if _RUN_ID.fullmatch(run_id) is None:
        raise ValueError("invalid_run_id")
    return root / ".pactkit/codex-sessions" / f"{run_id}.json"


def _load_thread(root: Path, run_id: str) -> str | None:
    path = _session_path(root, run_id)
    if not path.exists():
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("invalid_codex_session_state") from exc
    if (
        not isinstance(value, dict)
        or set(value) != {"run_id", "thread_id"}
        or value.get("run_id") != run_id
        or not isinstance(value.get("thread_id"), str)
        or not value["thread_id"]
    ):
        raise ValueError("invalid_codex_session_state")
    return value["thread_id"]


def _save_thread(root: Path, run_id: str, thread_id: str) -> None:
    if not isinstance(thread_id, str) or not thread_id:
        raise ValueError("invalid_thread_id")
    path = _session_path(root, run_id)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    try:
        path.parent.chmod(0o700)
        atomic_write(
            path,
            json.dumps(
                {"run_id": run_id, "thread_id": thread_id},
                ensure_ascii=False, separators=(",", ":"),
            ) + "\n",
        )
        path.chmod(0o600)
    except OSError as exc:
        raise ValueError("codex_session_state_unavailable") from exc


def main(argv: list[str] | None = None, *, adapter_factory: AdapterFactory = _default_adapter) -> int:
    parser = argparse.ArgumentParser(prog="pactkit-codex-work-unit")
    actions = parser.add_subparsers(dest="action", required=True)
    execute = actions.add_parser("execute", help="Execute exactly one leased Core WorkUnit")
    execute.add_argument("run_id")
    execute.add_argument("--owner", required=True)
    execute.add_argument("--idempotency-key", required=True)
    execute.add_argument("--thread-id")
    execute.add_argument(
        "--receipt", required=True,
        help="Candidate receipt template JSON or @path",
    )
    run = actions.add_parser(
        "run", help="Run successive Core WorkUnits in one resumable Codex thread",
    )
    run.add_argument("run_id")
    run.add_argument("--owner", required=True)
    run.add_argument("--max-units", type=int, default=32)
    run.add_argument("--thread-id")
    run.add_argument("--idempotency-prefix")
    run.add_argument(
        "--authorize", action="append", default=[],
        help="Explicitly authorize one Core-declared manual operation",
    )
    args = parser.parse_args(argv)
    root = Path.cwd()
    try:
        adapter = adapter_factory(root, args.owner)
        if args.action == "run":
            # A supplied thread wins only for first-time/manual recovery. Once
            # persisted, the run-bound thread is authoritative.
            persisted = _load_thread(root, args.run_id)
            if persisted is not None and args.thread_id not in (None, persisted):
                raise ValueError("codex_session_thread_conflict")
            # Core's human-oriented atomic-write diagnostics must not corrupt
            # this command's machine-readable stdout contract.
            with redirect_stdout(sys.stderr):
                result = adapter.run_session(
                    args.run_id, thread_id=persisted or args.thread_id,
                    max_units=args.max_units,
                    idempotency_prefix=args.idempotency_prefix,
                    authorized_operations=frozenset(args.authorize),
                )
                _save_thread(root, args.run_id, result.thread_id)
            print(json.dumps(asdict(result), ensure_ascii=False))
            return 0 if result.decision in {"done", "unit_limit", "await_user"} else 1

        def receipt_factory(unit, _terminal):
            if args.receipt is None:
                raise AssertionError("receipt_factory_not_requested")
            # Parse/read only after the adapter has leased a concrete unit. A
            # malformed template is therefore a recoverable, auditable host
            # attempt rather than an opaque CLI failure with no Core record.
            template = _receipt_template(args.receipt)
            return _receipt_from_template(template, unit, owner=args.owner, root=root)

        with redirect_stdout(sys.stderr):
            dispatched = adapter.execute(
                args.run_id,
                idempotency_key=args.idempotency_key,
                thread_id=args.thread_id,
                receipt_factory=receipt_factory,
            )
        print(json.dumps(asdict(dispatched), ensure_ascii=False))
        # A completed host turn is only transport success. Receipt acceptance
        # is decided by Core, and callers must receive a failing process status
        # when Core rejects the candidate so they can follow its retry decision.
        if dispatched.submission is not None and dispatched.submission.attempt_status != "succeeded":
            return 1
        return 0
    except (AppServerError, OSError, ValueError, WorkUnitError) as exc:
        print(f"Codex WorkUnit error: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
