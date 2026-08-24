"""Codex App Server adapter for Core-owned PactKit WorkUnits.

This module deliberately contains no workflow steps, evidence validators, or
completion rules.  It converts one Core-issued WorkUnit into one Codex turn and
records the host terminal event; the adapter must separately submit an
EvidenceReceipt to let Core advance the authoritative run.
"""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import asdict, dataclass, replace
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any, Callable

from pactkit.workflow_engine import (
    EvidenceReceipt,
    HostCapabilities,
    PlanFinalizer,
    SubmissionResult,
    WorkflowEngine,
    WorkflowFinalizer,
    WorkUnit,
)

from pactkit_codex.app_server import (
    AppServerApprovalRequired,
    AppServerError,
    AppServerProtocolError,
    CodexAppServer,
    TurnTerminal,
    app_server_capability,
)

ReceiptFactory = Callable[[WorkUnit, TurnTerminal], EvidenceReceipt]


def _adapter_version() -> str:
    """Return the adapter distribution version, never Core's version."""
    try:
        return f"pactkit-codex/{version('pactkit-codex')}"
    except PackageNotFoundError:
        # Editable source trees without installed metadata remain auditable
        # without falsely attributing the running adapter to PactKit Core.
        return "pactkit-codex/uninstalled"


ADAPTER_VERSION = _adapter_version()


@dataclass(frozen=True)
class DispatchedWorkUnit:
    """One App Server turn associated with one Core-issued WorkUnit."""

    unit: WorkUnit
    thread_id: str
    turn_id: str
    terminal_status: str
    submission: SubmissionResult | None = None


@dataclass(frozen=True)
class ManagedSessionResult:
    """Bounded result of a Core-driven sequence of Codex turns."""

    run_id: str
    thread_id: str
    decision: str
    dispatched: tuple[DispatchedWorkUnit, ...]


RECEIPT_OUTPUT_SCHEMA: dict[str, object] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        # Azure strict structured outputs reject open-ended object schemas.
        # Claims are step-specific, so carry their JSON representation in a
        # closed-schema string and parse it locally before Core validation.
        "claims_json": {"type": "string"},
        "evidence_files": {"type": "array", "items": {"type": "string"}},
        "result_refs": {"type": "array", "items": {"type": "string"}},
        "story_id": {"type": ["string", "null"]},
        "title": {"type": ["string", "null"]},
        "tasks": {"type": "array", "items": {"type": "string"}},
    },
    "required": [
        "claims_json", "evidence_files", "result_refs",
        "story_id", "title", "tasks",
    ],
}


class CodexWorkUnitAdapter:
    """Thin host adapter that never decides the next WorkUnit."""

    def __init__(self, engine: WorkflowEngine, app_server: CodexAppServer, *, owner: str) -> None:
        self.engine = engine
        self.app_server = app_server
        self.owner = owner

    def execute(
        self, run_id: str, *, idempotency_key: str, thread_id: str | None = None,
        receipt_factory: ReceiptFactory | None = None,
    ) -> DispatchedWorkUnit:
        """Acquire one unit, execute one turn, then let Core validate explicit evidence.

        ``receipt_factory`` is intentionally supplied by the caller rather than
        derived from model prose.  Its result remains an untrusted candidate and
        is submitted only to Core's canonical validator.
        """
        unit = self.engine.acquire(
            run_id, owner=self.owner, idempotency_key=idempotency_key,
        )
        started_at = time.time()
        active_thread: str | None = None
        started_turn: str | None = None
        try:
            self.app_server.connect()
            active_thread = (
                self.app_server.resume_thread(thread_id)
                if thread_id is not None
                else self.app_server.start_thread()
            )
            started = self.app_server.start_turn(active_thread, self._prompt(unit))
            started_turn = started.turn_id
            terminal = self.app_server.wait_for_turn(started.turn_id)
            terminal_status = self._attempt_terminal(terminal.status)
            capabilities = self._core_capabilities()
            submission = None
            if terminal_status == "succeeded" and receipt_factory is not None:
                try:
                    candidate = receipt_factory(unit, terminal)
                    receipt = replace(
                        candidate,
                        host="codex",
                        capabilities=asdict(capabilities),
                        thread_ref=active_thread,
                        turn_ref=started.turn_id,
                        adapter_version=ADAPTER_VERSION,
                        started_at=started_at,
                    )
                except Exception:
                    self.engine.record_turn_terminal(
                        run_id,
                        unit_id=unit.unit_id,
                        unit_version=unit.version,
                        owner=self.owner,
                        host="codex",
                        status="malformed_result",
                        thread=active_thread,
                        turn=started.turn_id,
                        capabilities=capabilities,
                        failure_reason="receipt_construction_failed",
                        started_at=started_at,
                        adapter_version=ADAPTER_VERSION,
                    )
                    raise
                self.engine.record_turn_terminal(
                    run_id,
                    unit_id=unit.unit_id,
                    unit_version=unit.version,
                    owner=self.owner,
                    host="codex",
                    status=terminal_status,
                    thread=active_thread,
                    turn=started.turn_id,
                    capabilities=capabilities,
                    started_at=started_at,
                    adapter_version=ADAPTER_VERSION,
                )
                submission = self.engine.submit(
                    unit.unit_id,
                    receipt,
                    owner=self.owner,
                    idempotency_key=f"{idempotency_key}:submit",
                )
            else:
                self.engine.record_turn_terminal(
                    run_id,
                    unit_id=unit.unit_id,
                    unit_version=unit.version,
                    owner=self.owner,
                    host="codex",
                    status=terminal_status,
                    thread=active_thread,
                    turn=started.turn_id,
                    capabilities=capabilities,
                    started_at=started_at,
                    adapter_version=ADAPTER_VERSION,
                )
            return DispatchedWorkUnit(
                unit=unit,
                thread_id=active_thread,
                turn_id=started.turn_id,
                terminal_status=terminal_status,
                submission=submission,
            )
        except AppServerError as exc:
            awaiting_approval = isinstance(exc, AppServerApprovalRequired)
            self.engine.record_turn_terminal(
                run_id,
                unit_id=unit.unit_id,
                unit_version=unit.version,
                owner=self.owner,
                host="codex",
                status="awaiting_approval" if awaiting_approval else "host_error",
                thread=active_thread,
                turn=started_turn,
                capabilities=self._core_capabilities(),
                failure_reason=(
                    "app_server_approval_required" if awaiting_approval
                    else "app_server_protocol_error"
                    if isinstance(exc, AppServerProtocolError)
                    else "app_server_unavailable"
                ),
                started_at=started_at,
                adapter_version=ADAPTER_VERSION,
            )
            raise
        finally:
            self.app_server.close()

    def run_session(
        self, run_id: str, *, thread_id: str | None = None, max_units: int = 32,
        idempotency_prefix: str | None = None,
        authorized_operations: frozenset[str] = frozenset(),
    ) -> ManagedSessionResult:
        """Execute successive Core-issued units in one App Server thread.

        Core remains the scheduler: this loop advances only after an accepted
        Receipt. A rejection, approval request, malformed result, or host
        failure terminates the bounded session with a recoverable decision.
        """
        if isinstance(max_units, bool) or not isinstance(max_units, int) or max_units <= 0:
            raise ValueError("invalid_max_units")
        if idempotency_prefix is not None and (
            not isinstance(idempotency_prefix, str) or not idempotency_prefix
        ):
            raise ValueError("invalid_idempotency_prefix")
        idempotency_namespace = self._idempotency_namespace(idempotency_prefix)
        dispatched: list[DispatchedWorkUnit] = []
        active_thread: str | None = None
        self.app_server.connect()
        try:
            active_thread = (
                self.app_server.resume_thread(thread_id)
                if thread_id is not None
                else self.app_server.start_thread()
            )
            for index in range(max_units):
                status = self.engine.status(run_id)
                if status["status"] == "completed":
                    return ManagedSessionResult(
                        run_id, active_thread, "done", tuple(dispatched),
                    )
                key = f"{idempotency_namespace}:{status['step_id']}:{index}"
                unit = self.engine.lease_current(
                    run_id, owner=self.owner, idempotency_key=key,
                )
                started_at = time.time()
                started_turn: str | None = None
                missing_authorization = set(unit.manual_authorization) - authorized_operations
                if missing_authorization:
                    self._record_terminal(
                        run_id, unit, "awaiting_approval", active_thread, None, started_at,
                        failure_reason="manual_authorization_required:"
                        + ",".join(sorted(missing_authorization)),
                    )
                    dispatched.append(DispatchedWorkUnit(
                        unit, active_thread, "not-started", "awaiting_approval", None,
                    ))
                    return ManagedSessionResult(
                        run_id, active_thread, "await_user", tuple(dispatched),
                    )
                try:
                    started = self.app_server.start_turn(
                        active_thread, self._prompt(unit),
                        output_schema=RECEIPT_OUTPUT_SCHEMA,
                    )
                    started_turn = started.turn_id
                    terminal = self.app_server.wait_for_turn(
                        started.turn_id, thread_id=active_thread, require_output=True,
                    )
                    terminal_status = self._attempt_terminal(terminal.status)
                    if terminal_status != "succeeded":
                        self._record_terminal(
                            run_id, unit, terminal_status, active_thread,
                            started.turn_id, started_at,
                            failure_reason=self._terminal_failure_reason(terminal.status),
                        )
                        dispatched.append(DispatchedWorkUnit(
                            unit, active_thread, started.turn_id, terminal_status, None,
                        ))
                        return ManagedSessionResult(
                            run_id, active_thread, "retry", tuple(dispatched),
                        )
                    try:
                        payload = self._structured_payload(terminal.output_text)
                        if unit.step_id == "story_identity":
                            story_id = payload.get("story_id")
                            if not isinstance(story_id, str) or not story_id:
                                raise ValueError("structured_result_missing_story_id")
                            self.engine.bind_story(
                                run_id, story_id=story_id, owner=self.owner,
                                idempotency_key=f"{key}:bind-story",
                            )
                        receipt = self._receipt_from_payload(
                            unit, payload, active_thread, started.turn_id, started_at,
                        )
                    except Exception:
                        self._record_terminal(
                            run_id, unit, "malformed_result", active_thread,
                            started.turn_id, started_at,
                            failure_reason="structured_result_invalid",
                        )
                        dispatched.append(DispatchedWorkUnit(
                            unit, active_thread, started.turn_id, "malformed_result", None,
                        ))
                        return ManagedSessionResult(
                            run_id, active_thread, "retry", tuple(dispatched),
                        )
                    self._record_terminal(
                        run_id, unit, "succeeded", active_thread,
                        started.turn_id, started_at,
                    )
                    if unit.step_id == "finalize_plan":
                        story_id = payload.get("story_id")
                        title = payload.get("title")
                        tasks = payload.get("tasks")
                        if (
                            not isinstance(story_id, str) or not story_id
                            or not isinstance(title, str) or not title.strip()
                            or not isinstance(tasks, list) or not tasks
                            or not all(isinstance(task, str) and task.strip() for task in tasks)
                        ):
                            self.engine.reject(
                                unit.unit_id, owner=self.owner,
                                reason_code="finalize_result_invalid",
                            )
                            raise ValueError("structured_result_invalid_finalize")
                        PlanFinalizer(Path(self.engine.root), self.engine).finalize(
                            run_id, story_id=story_id, title=title, tasks=tasks,
                            idempotency_key=self._finalize_idempotency_key(unit),
                        )
                        dispatched.append(DispatchedWorkUnit(
                            unit, active_thread, started.turn_id, terminal_status, None,
                        ))
                        return ManagedSessionResult(
                            run_id, active_thread, "done", tuple(dispatched),
                        )
                    if unit.step_id.startswith("finalize_") or unit.step_id == "finalize_workflow":
                        WorkflowFinalizer(Path(self.engine.root), self.engine).finalize(
                            run_id, receipt, owner=self.owner,
                            idempotency_key=self._finalize_idempotency_key(unit),
                        )
                        dispatched.append(DispatchedWorkUnit(
                            unit, active_thread, started.turn_id, terminal_status, None,
                        ))
                        return ManagedSessionResult(
                            run_id, active_thread, "done", tuple(dispatched),
                        )
                    submission = self.engine.submit(
                        unit.unit_id, receipt, owner=self.owner,
                        idempotency_key=f"{key}:submit",
                    )
                    dispatched.append(DispatchedWorkUnit(
                        unit, active_thread, started.turn_id, terminal_status, submission,
                    ))
                    if submission.attempt_status != "succeeded":
                        return ManagedSessionResult(
                            run_id, active_thread, submission.decision, tuple(dispatched),
                        )
                except AppServerError as exc:
                    self._record_terminal(
                        run_id, unit,
                        "awaiting_approval"
                        if isinstance(exc, AppServerApprovalRequired) else "host_error",
                        active_thread, started_turn, started_at,
                        failure_reason=(
                            "app_server_approval_required"
                            if isinstance(exc, AppServerApprovalRequired)
                            else "app_server_protocol_error"
                            if isinstance(exc, AppServerProtocolError)
                            else "app_server_unavailable"
                        ),
                    )
                    raise
            return ManagedSessionResult(
                run_id, active_thread, "unit_limit", tuple(dispatched),
            )
        finally:
            self.app_server.close()

    @staticmethod
    def _idempotency_namespace(prefix: str | None) -> str:
        """Return a stable namespace for one invocation, unique by default."""
        if prefix is not None:
            return prefix
        return f"codex-session:{uuid.uuid4().hex}"

    @staticmethod
    def _finalize_idempotency_key(unit: WorkUnit) -> str:
        """Bind the journal transaction to the immutable Unit generation."""
        return f"{unit.unit_id}-v{unit.version}"

    def _record_terminal(
        self, run_id: str, unit: WorkUnit, status: str, thread: str | None,
        turn: str | None, started_at: float, failure_reason: str | None = None,
    ) -> None:
        self.engine.record_turn_terminal(
            run_id, unit_id=unit.unit_id, unit_version=unit.version,
            owner=self.owner, host="codex", status=status, thread=thread,
            turn=turn, capabilities=self._core_capabilities(),
            failure_reason=failure_reason, started_at=started_at,
            adapter_version=ADAPTER_VERSION,
        )

    @staticmethod
    def _structured_payload(raw: str | None) -> dict[str, Any]:
        if not isinstance(raw, str) or not raw.strip():
            raise ValueError("structured_result_missing")
        try:
            value = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError("structured_result_invalid_json") from exc
        allowed = {
            "claims_json", "evidence_files", "result_refs",
            "story_id", "title", "tasks",
        }
        if not isinstance(value, dict) or set(value) != allowed:
            raise ValueError("structured_result_invalid_fields")
        claims_json = value.get("claims_json")
        if not isinstance(claims_json, str):
            raise ValueError("structured_result_invalid_claims")
        try:
            claims = json.loads(claims_json)
        except json.JSONDecodeError as exc:
            raise ValueError("structured_result_invalid_claims_json") from exc
        if not isinstance(claims, dict):
            raise ValueError("structured_result_invalid_claims")
        for field in ("evidence_files", "result_refs", "tasks"):
            items = value.get(field, [])
            if not isinstance(items, list) or not all(
                isinstance(item, str) and item for item in items
            ):
                raise ValueError(f"structured_result_invalid_{field}")
        return {**value, "claims": claims}

    def _receipt_from_payload(
        self, unit: WorkUnit, payload: dict[str, Any], thread_id: str,
        turn_id: str, started_at: float,
    ) -> EvidenceReceipt:
        receipt = EvidenceReceipt.for_files(
            unit, owner=self.owner, root=Path(self.engine.root),
            files=payload.get("evidence_files", []),
            claims=dict(payload.get("claims", {})),
        )
        return replace(
            receipt, host="codex", capabilities=asdict(self._core_capabilities()),
            thread_ref=thread_id, turn_ref=turn_id, adapter_version=ADAPTER_VERSION,
            result_refs=tuple(payload.get("result_refs", [])), started_at=started_at,
        )

    @staticmethod
    def _attempt_terminal(app_server_status: str) -> str:
        if app_server_status == "completed":
            return "succeeded"
        if app_server_status == "interrupted":
            return "interrupted"
        return "host_error"

    @staticmethod
    def _terminal_failure_reason(app_server_status: str) -> str:
        if app_server_status == "interrupted":
            return "turn_interrupted"
        return "turn_failed"

    @staticmethod
    def _core_capabilities() -> HostCapabilities:
        """Map adapter capability names to the Core protocol schema."""
        capability = app_server_capability()
        return HostCapabilities(
            host="codex",
            protocol_version=int(capability["protocol_version"]),
            discovery_source=str(capability["verification_source"]),
            structured_results=bool(capability["structured_results"]),
            tool_execution=bool(capability["tool_execution"]),
            approval=bool(capability["approval"]),
            lifecycle_events=bool(capability["lifecycle_events"]),
            thread_resume=bool(capability["thread_resume"]),
            turn_steer=bool(capability["turn_steer"]),
            background_execution=bool(capability["background_execution"]),
            cancellation=bool(capability["cancellation"]),
            e2e_validated=bool(capability["e2e_validated"]),
        )

    @staticmethod
    def _prompt(unit: WorkUnit) -> str:
        """Render the Core-owned contract without adding workflow semantics."""
        return (
            "Execute exactly this PactKit WorkUnit. Do not choose another workflow step, "
            "write outside the allowed scope, or claim workflow completion. Return evidence "
            "for Core validation. Encode the step-specific claims object as JSON in the "
            "claims_json string field of the required structured response.\n\n"
            "Set evidence_files to exactly the repository-relative files changed by this "
            "WorkUnit and permitted by allowed_writes; use an empty array when no file was "
            "changed. Never include directories, absolute paths, or files merely read.\n\n"
            f"unit_id: {unit.unit_id}\n"
            f"unit_version: {unit.version}\n"
            f"workflow_id: {unit.workflow_id}\n"
            f"step_id: {unit.step_id}\n"
            f"objective: {unit.objective}\n"
            f"allowed_reads: {', '.join(unit.allowed_reads) or '(none)'}\n"
            f"allowed_writes: {', '.join(unit.allowed_writes) or '(none)'}\n"
            f"forbidden_operations: {', '.join(unit.forbidden_operations) or '(none)'}\n"
            f"acceptance_commands: {', '.join(unit.acceptance_commands) or '(none)'}\n"
            f"required_claims: {'; '.join(unit.required_claims) or '(none)'}\n"
            f"manual_authorization: {', '.join(unit.manual_authorization) or '(none)'}"
        )
