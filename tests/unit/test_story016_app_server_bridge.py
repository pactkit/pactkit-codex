import io
import json

import pytest


class _FakeProcess:
    def __init__(self, messages):
        self.stdin = io.StringIO()
        self.stdout = io.StringIO("".join(json.dumps(message) + "\n" for message in messages))
        self.stderr = io.StringIO()
        self.returncode = None
        self.terminated = False

    def poll(self):
        return self.returncode

    def terminate(self):
        self.terminated = True
        self.returncode = 0

    def wait(self, timeout=None):
        self.returncode = 0
        return 0


_PLAN_SPEC = """# STORY-slim-995: Managed Plan\n\n| Field | Value |\n|-------|-------|\n| ID | STORY-slim-995 |\n| Status | In Progress |\n| Priority | P0 |\n| Release | 2.21.0 |\n\n## Background\n\nA managed Plan workflow requires a self-contained specification fixture.\n\n## Requirements\n\n### R1: Finalize through Core (MUST)\n\nThe Core finalizer MUST validate the specification and publish its governance facts.\n\n## Acceptance Criteria\n\n### AC1: Core finalization succeeds (R1)\n\n- **Given** a lintable Spec and a valid HLD\n- **When** the managed adapter submits its terminal receipt\n- **Then** Core creates the Story, Board, context, and completion journal\n\n## Security Scope\n\n### SEC-1: Governance write integrity\n\nThe finalizer MUST validate repository evidence before writing governed projections.\n"""


def _prepare_finalize_run(root):
    from pactkit.workflow_engine import EvidenceReceipt, WorkflowEngine

    config = root / ".codex/pactkit.yaml"
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text("developer: test\n", encoding="utf-8")
    (root / "docs/product/stories").mkdir(parents=True, exist_ok=True)
    # Keep the fixture equivalent to an initialized project so Core's real
    # Plan preflight validator remains part of this finalizer test.
    (root / "docs/product/sprint_board.md").write_text(
        "# Sprint Board\n", encoding="utf-8",
    )
    story_id = "STORY-slim-995"
    spec = root / f"docs/specs/{story_id}.md"
    spec.parent.mkdir(parents=True, exist_ok=True)
    spec.write_text(_PLAN_SPEC, encoding="utf-8")
    hld = root / "docs/architecture/graphs/system_design.mmd"
    hld.parent.mkdir(parents=True, exist_ok=True)
    hld.write_text("flowchart TD\n  A --> B\n", encoding="utf-8")
    engine = WorkflowEngine(root)
    run = engine.start("project-plan", goal="plan", story_id=story_id)
    claims = {
        "preflight": {"guard": "pass"},
        "clarification": {"clarification_resolved": True},
        "archaeology": {"trace": ["workflow_engine"]},
        "story_identity": {"story_id": story_id},
        "spec_scaffold": {}, "spec_content": {},
        "spec_security": {"security_scoped": True}, "spec_lint": {},
    }
    files = {
        "spec_scaffold": [f"docs/specs/{story_id}.md"],
        "spec_content": [f"docs/specs/{story_id}.md", "docs/architecture/graphs/system_design.mmd"],
        "spec_security": [f"docs/specs/{story_id}.md"],
        "spec_lint": [f"docs/specs/{story_id}.md"],
    }
    while engine.status(run.run_id)["step_id"] != "finalize_plan":
        step = engine.status(run.run_id)["step_id"]
        unit = engine.acquire(run.run_id, owner="codex", idempotency_key=f"a-{step}")
        receipt = EvidenceReceipt.for_files(
            unit, owner="codex", root=root, files=files.get(step, []), claims=claims[step],
        )
        result = engine.submit(
            unit.unit_id, receipt, owner="codex", idempotency_key=f"s-{step}",
        )
        assert result.attempt_status == "succeeded", f"{step}: {result.reason_code}"
    return engine, run, story_id


def _managed_result(claims, **overrides):
    result = {
        "claims_json": json.dumps(claims),
        "evidence_files": [],
        "result_refs": [],
        "story_id": None,
        "title": None,
        "tasks": [],
    }
    result.update(overrides)
    return result


def test_receipt_schema_is_azure_strict_and_claims_are_json_encoded():
    from pactkit_codex.work_unit_adapter import (
        RECEIPT_OUTPUT_SCHEMA,
        CodexWorkUnitAdapter,
    )

    assert RECEIPT_OUTPUT_SCHEMA["additionalProperties"] is False
    assert RECEIPT_OUTPUT_SCHEMA["properties"]["claims_json"] == {"type": "string"}
    assert "claims" not in RECEIPT_OUTPUT_SCHEMA["properties"]
    payload = CodexWorkUnitAdapter._structured_payload(
        json.dumps(_managed_result({"guard": "pass"})),
    )
    assert payload["claims"] == {"guard": "pass"}


@pytest.mark.parametrize("claims_json", ["not-json", "[]", "null", '"text"'])
def test_structured_payload_rejects_invalid_or_non_object_claims(claims_json):
    from pactkit_codex.work_unit_adapter import CodexWorkUnitAdapter

    with pytest.raises(ValueError, match="structured_result_invalid_claims"):
        CodexWorkUnitAdapter._structured_payload(
            json.dumps(_managed_result({}, claims_json=claims_json)),
        )


def test_app_server_bridge_runs_initialize_thread_turn_and_terminal_event(tmp_path):
    from pactkit_codex.app_server import CodexAppServer

    process = _FakeProcess([
        {"id": 1, "result": {"platformFamily": "macos"}},
        {"id": 2, "result": {"thread": {"id": "thr_123"}}},
        {"id": 3, "result": {"turn": {"id": "turn_456"}}},
        {"method": "turn/completed", "params": {
            "turn": {"id": "turn_456", "status": "completed"},
        }},
    ])
    bridge = CodexAppServer(
        cwd=tmp_path, process_factory=lambda *_args, **_kwargs: process,
    )

    bridge.connect()
    thread_id = bridge.start_thread()
    turn = bridge.start_turn(thread_id, "Execute the supplied WorkUnit only.")
    terminal = bridge.wait_for_turn(turn.turn_id)

    assert thread_id == "thr_123"
    assert turn.thread_id == "thr_123"
    assert terminal.status == "completed"
    sent = [json.loads(line) for line in process.stdin.getvalue().splitlines()]
    assert [message["method"] for message in sent] == [
        "initialize", "initialized", "thread/start", "turn/start",
    ]
    assert "params" not in sent[1]
    assert sent[3]["params"]["threadId"] == "thr_123"
    bridge.close()
    assert process.terminated is True


def test_app_server_bridge_collects_structured_result_from_same_turn(tmp_path):
    from pactkit_codex.app_server import CodexAppServer

    result = {"claims": {"guard": "pass"}, "evidence_files": []}
    process = _FakeProcess([
        {"id": 1, "result": {}},
        {"id": 2, "result": {"thread": {"id": "thr_123"}}},
        {"id": 3, "result": {"turn": {"id": "turn_456"}}},
        {"method": "item/completed", "params": {
            "threadId": "thr_other", "turnId": "turn_other",
            "completedAtMs": 1,
            "item": {"id": "msg_wrong", "type": "agentMessage", "text": "{}"},
        }},
        {"method": "item/completed", "params": {
            "threadId": "thr_123", "turnId": "turn_456",
            "completedAtMs": 2,
            "item": {
                "id": "msg_receipt", "type": "agentMessage",
                "text": json.dumps(result),
            },
        }},
        {"method": "turn/completed", "params": {
            "threadId": "thr_123",
            "turn": {"id": "turn_456", "status": "completed", "items": []},
        }},
    ])
    bridge = CodexAppServer(
        cwd=tmp_path, process_factory=lambda *_args, **_kwargs: process,
    )
    schema = {"type": "object", "additionalProperties": False}

    bridge.connect()
    thread_id = bridge.start_thread()
    turn = bridge.start_turn(thread_id, "execute", output_schema=schema)
    terminal = bridge.wait_for_turn(turn.turn_id, thread_id=thread_id)

    assert terminal.output_text == json.dumps(result)
    request = [
        message for message in map(json.loads, process.stdin.getvalue().splitlines())
        if message.get("method") == "turn/start"
    ][0]
    assert request["params"]["outputSchema"] == schema


def test_app_server_bridge_uses_last_structured_result_from_same_turn(tmp_path):
    from pactkit_codex.app_server import CodexAppServer

    process = _FakeProcess([
        {"id": 1, "result": {}},
        {"method": "item/completed", "params": {
            "threadId": "thr_123", "turnId": "turn_456",
            "completedAtMs": 1,
            "item": {"id": "one", "type": "agentMessage", "text": "{}"},
        }},
        {"method": "item/completed", "params": {
            "threadId": "thr_123", "turnId": "turn_456",
            "completedAtMs": 2,
            "item": {"id": "two", "type": "agentMessage", "text": "{\"claims\":{}}"},
        }},
        {"method": "turn/completed", "params": {
            "threadId": "thr_123",
            "turn": {"id": "turn_456", "status": "completed", "items": []},
        }},
    ])
    bridge = CodexAppServer(
        cwd=tmp_path, process_factory=lambda *_args, **_kwargs: process,
    )
    bridge.connect()

    terminal = bridge.wait_for_turn("turn_456", thread_id="thr_123")

    assert terminal.output_text == '{"claims":{}}'


def test_app_server_bridge_uses_last_json_object_inside_one_agent_message(tmp_path):
    from pactkit_codex.app_server import CodexAppServer

    process = _FakeProcess([
        {"id": 1, "result": {}},
        {"method": "item/completed", "params": {
            "threadId": "thr_123", "turnId": "turn_456",
            "item": {"id": "two-in-one", "type": "agentMessage", "text": (
                '{"claims_json":"{}"}\n'
                '{"claims_json":"{\\"guard\\":\\"pass\\"}"}'
            )},
        }},
        {"method": "turn/completed", "params": {
            "threadId": "thr_123",
            "turn": {"id": "turn_456", "status": "completed", "items": []},
        }},
    ])
    bridge = CodexAppServer(
        cwd=tmp_path, process_factory=lambda *_args, **_kwargs: process,
    )
    bridge.connect()

    terminal = bridge.wait_for_turn("turn_456", thread_id="thr_123")

    assert json.loads(terminal.output_text) == {
        "claims_json": json.dumps({"guard": "pass"}, separators=(",", ":")),
    }


def test_work_unit_prompt_requires_exact_evidence_contract(tmp_path):
    from pactkit.workflow_engine import WorkUnit
    from pactkit_codex.work_unit_adapter import CodexWorkUnitAdapter

    unit = WorkUnit(
        run_id="run-" + "a" * 32, unit_id="unit-" + "b" * 32,
        workflow_id="project-plan", step_id="spec_content", version=1,
        objective="Write requirements and acceptance criteria", input_refs=(),
        allowed_reads=("docs/**", "src/**"),
        allowed_writes=("docs/specs/STORY-slim-999.md",
                        "docs/architecture/graphs/system_design.mmd"),
        forbidden_operations=("update_board", "external_write"),
        acceptance_commands=("receipt:requirements", "receipt:acceptance"),
        manual_authorization=(), lease_owner="codex", lease_expires_at=9999999999,
        required_claims=("evidence_files must exactly equal allowed_writes",
                         "system_design.mmd must contain a valid Mermaid graph or flowchart"),
    )

    prompt = CodexWorkUnitAdapter._prompt(unit)

    assert "evidence_files must exactly equal allowed_writes" in prompt
    assert "valid Mermaid graph or flowchart" in prompt


def test_app_server_bridge_ignores_empty_intermediate_agent_message(tmp_path):
    from pactkit_codex.app_server import CodexAppServer

    process = _FakeProcess([
        {"id": 1, "result": {}},
        {"method": "item/completed", "params": {
            "threadId": "thr_123", "turnId": "turn_456",
            "item": {"type": "agentMessage", "text": ""},
        }},
        {"method": "item/completed", "params": {
            "threadId": "thr_123", "turnId": "turn_456",
            "item": {"type": "agentMessage", "text": "{}"},
        }},
        {"method": "turn/completed", "params": {
            "threadId": "thr_123",
            "turn": {"id": "turn_456", "status": "completed"},
        }},
    ])
    bridge = CodexAppServer(
        cwd=tmp_path, process_factory=lambda *_args, **_kwargs: process,
    )
    bridge.connect()

    assert bridge.wait_for_turn("turn_456", thread_id="thr_123").output_text == "{}"


def test_app_server_bridge_rejects_completed_turn_without_structured_result(tmp_path):
    from pactkit_codex.app_server import AppServerProtocolError, CodexAppServer

    process = _FakeProcess([
        {"id": 1, "result": {}},
        {"method": "turn/completed", "params": {
            "threadId": "thr_123",
            "turn": {"id": "turn_456", "status": "completed"},
        }},
    ])
    bridge = CodexAppServer(
        cwd=tmp_path, process_factory=lambda *_args, **_kwargs: process,
    )
    bridge.connect()

    with pytest.raises(AppServerProtocolError, match="missing_structured_result"):
        bridge.wait_for_turn(
            "turn_456", thread_id="thr_123", require_output=True,
        )


def test_app_server_bridge_resumes_thread_and_fails_closed_on_protocol_error(tmp_path):
    from pactkit_codex.app_server import AppServerProtocolError, CodexAppServer

    process = _FakeProcess([
        {"id": 1, "result": {}},
        {"id": 2, "error": {"code": -1, "message": "unknown thread"}},
    ])
    bridge = CodexAppServer(
        cwd=tmp_path, process_factory=lambda *_args, **_kwargs: process,
    )

    bridge.connect()
    with pytest.raises(AppServerProtocolError, match="unknown thread"):
        bridge.resume_thread("thr_missing")


def test_app_server_bridge_steers_the_expected_active_turn(tmp_path):
    from pactkit_codex.app_server import CodexAppServer

    process = _FakeProcess([
        {"id": 1, "result": {}},
        {"id": 2, "result": {"turnId": "turn_456"}},
    ])
    bridge = CodexAppServer(
        cwd=tmp_path, process_factory=lambda *_args, **_kwargs: process,
    )

    bridge.connect()
    assert bridge.steer_turn("thr_123", "turn_123", "continue") == "turn_456"

    request = json.loads(process.stdin.getvalue().splitlines()[-1])
    assert request["method"] == "turn/steer"
    assert request["params"]["threadId"] == "thr_123"
    assert request["params"]["expectedTurnId"] == "turn_123"


def test_app_server_bridge_reports_live_e2e_validated_resumable_mode():
    from pactkit_codex.app_server import app_server_capability

    capability = app_server_capability()

    assert capability["thread_resume"] is True
    assert capability["lifecycle_events"] is True
    assert capability["approval"] is False
    assert capability["e2e_validated"] is True
    assert capability["execution_mode"] == "resumable"


def test_work_unit_adapter_acquires_core_unit_and_records_turn_terminal(tmp_path):
    from pactkit.workflow_engine import WorkflowEngine
    from pactkit_codex.app_server import CodexAppServer
    from pactkit_codex.work_unit_adapter import CodexWorkUnitAdapter

    config = tmp_path / ".codex/pactkit.yaml"
    config.parent.mkdir(parents=True)
    config.write_text("developer: test\n", encoding="utf-8")
    (tmp_path / "docs/product/stories").mkdir(parents=True)
    (tmp_path / "docs/architecture/graphs").mkdir(parents=True)
    engine = WorkflowEngine(tmp_path)
    run = engine.start("project-plan", goal="plan")
    process = _FakeProcess([
        {"id": 1, "result": {}},
        {"id": 2, "result": {"thread": {"id": "thr_123"}}},
        {"id": 3, "result": {"turn": {"id": "turn_456"}}},
        {"method": "turn/completed", "params": {
            "turn": {"id": "turn_456", "status": "completed"},
        }},
    ])
    bridge = CodexAppServer(
        cwd=tmp_path, process_factory=lambda *_args, **_kwargs: process,
    )
    adapter = CodexWorkUnitAdapter(engine, bridge, owner="codex")

    dispatched = adapter.execute(run.run_id, idempotency_key="acquire-1")

    assert dispatched.unit.step_id == "preflight"
    assert dispatched.thread_id == "thr_123"
    assert dispatched.turn_id == "turn_456"
    attempt = engine._read(run.run_id)["attempts"][-1]
    assert attempt["unit_id"] == dispatched.unit.unit_id
    assert attempt["unit_version"] == dispatched.unit.version
    assert attempt["host"] == "codex"
    assert attempt["status"] == "succeeded"
    assert attempt["adapter_version"].startswith("pactkit-codex/")
    assert attempt["thread_ref"].startswith("sha256:")
    prompt = json.loads(process.stdin.getvalue().splitlines()[3])["params"]["input"][0]["text"]
    assert dispatched.unit.unit_id in prompt
    assert "preflight" in prompt


def test_adapter_version_comes_from_its_own_distribution(monkeypatch):
    import pactkit_codex.work_unit_adapter as adapter

    monkeypatch.setattr(adapter, "version", lambda package: "7.8.9")

    assert adapter._adapter_version() == "pactkit-codex/7.8.9"


def test_work_unit_adapter_submits_only_explicit_structured_receipt(tmp_path):
    from pactkit.workflow_engine import EvidenceReceipt, WorkflowEngine
    from pactkit_codex.app_server import CodexAppServer
    from pactkit_codex.work_unit_adapter import CodexWorkUnitAdapter

    config = tmp_path / ".codex/pactkit.yaml"
    config.parent.mkdir(parents=True)
    config.write_text("developer: test\n", encoding="utf-8")
    (tmp_path / "docs/product/stories").mkdir(parents=True)
    (tmp_path / "docs/architecture/graphs").mkdir(parents=True)
    engine = WorkflowEngine(tmp_path)
    run = engine.start("project-plan", goal="plan")
    process = _FakeProcess([
        {"id": 1, "result": {}},
        {"id": 2, "result": {"thread": {"id": "thr_123"}}},
        {"id": 3, "result": {"turn": {"id": "turn_456"}}},
        {"method": "turn/completed", "params": {
            "turn": {"id": "turn_456", "status": "completed"},
        }},
    ])
    bridge = CodexAppServer(
        cwd=tmp_path, process_factory=lambda *_args, **_kwargs: process,
    )
    adapter = CodexWorkUnitAdapter(engine, bridge, owner="codex")

    dispatched = adapter.execute(
        run.run_id,
        idempotency_key="acquire-1",
        receipt_factory=lambda unit, _terminal: EvidenceReceipt.for_files(
            unit, owner="codex", root=tmp_path, files=[], claims={"guard": "pass"},
        ),
    )

    assert dispatched.submission is not None
    assert dispatched.submission.attempt_status == "succeeded"
    assert engine.status(run.run_id)["step_id"] == "clarification"
    attempts = engine._read(run.run_id)["attempts"]
    assert attempts[-1]["host"] == "codex"
    assert attempts[-1]["thread_ref"].startswith("sha256:")
    assert attempts[-1]["execution_mode"] == "resumable"


def test_managed_session_reuses_one_thread_and_runs_until_core_next_step(tmp_path):
    from pactkit.workflow_engine import WorkflowEngine
    from pactkit_codex.app_server import CodexAppServer
    from pactkit_codex.work_unit_adapter import CodexWorkUnitAdapter

    config = tmp_path / ".codex/pactkit.yaml"
    config.parent.mkdir(parents=True)
    config.write_text("developer: test\n", encoding="utf-8")
    (tmp_path / "docs/product/stories").mkdir(parents=True)
    (tmp_path / "docs/architecture/graphs").mkdir(parents=True)
    engine = WorkflowEngine(tmp_path)
    run = engine.start("project-plan", goal="plan")
    process = _FakeProcess([
        {"id": 1, "result": {}},
        {"id": 2, "result": {"thread": {"id": "thr_123"}}},
        {"id": 3, "result": {"turn": {"id": "turn_1"}}},
        {"method": "item/completed", "params": {
            "threadId": "thr_123", "turnId": "turn_1", "completedAtMs": 1,
            "item": {"id": "msg_1", "type": "agentMessage", "text": json.dumps(
                _managed_result({"guard": "pass"}),
            )},
        }},
        {"method": "turn/completed", "params": {
            "threadId": "thr_123",
            "turn": {"id": "turn_1", "status": "completed", "items": []},
        }},
        {"id": 4, "result": {"turn": {"id": "turn_2"}}},
        {"method": "item/completed", "params": {
            "threadId": "thr_123", "turnId": "turn_2", "completedAtMs": 2,
            "item": {"id": "msg_2", "type": "agentMessage", "text": json.dumps(
                _managed_result({"clarification_resolved": True}),
            )},
        }},
        {"method": "turn/completed", "params": {
            "threadId": "thr_123",
            "turn": {"id": "turn_2", "status": "completed", "items": []},
        }},
    ])
    adapter = CodexWorkUnitAdapter(
        engine,
        CodexAppServer(cwd=tmp_path, process_factory=lambda *_args, **_kwargs: process),
        owner="codex",
    )

    result = adapter.run_session(run.run_id, max_units=2)

    assert result.thread_id == "thr_123"
    assert [item.unit.step_id for item in result.dispatched] == [
        "preflight", "clarification",
    ]
    assert result.decision == "unit_limit"
    assert engine.status(run.run_id)["step_id"] == "archaeology"
    sent = [json.loads(line) for line in process.stdin.getvalue().splitlines()]
    assert [item["method"] for item in sent].count("thread/start") == 1
    assert [item["method"] for item in sent].count("thread/resume") == 0
    turns = [item for item in sent if item["method"] == "turn/start"]
    assert [item["params"]["threadId"] for item in turns] == ["thr_123", "thr_123"]
    assert all("outputSchema" in item["params"] for item in turns)
    assert process.terminated is True


def test_managed_session_stops_on_rejected_receipt_without_next_unit(tmp_path):
    from pactkit.workflow_engine import WorkflowEngine
    from pactkit_codex.app_server import CodexAppServer
    from pactkit_codex.work_unit_adapter import CodexWorkUnitAdapter

    config = tmp_path / ".codex/pactkit.yaml"
    config.parent.mkdir(parents=True)
    config.write_text("developer: test\n", encoding="utf-8")
    (tmp_path / "docs/product/stories").mkdir(parents=True)
    (tmp_path / "docs/architecture/graphs").mkdir(parents=True)
    engine = WorkflowEngine(tmp_path)
    run = engine.start("project-plan", goal="plan")
    process = _FakeProcess([
        {"id": 1, "result": {}},
        {"id": 2, "result": {"thread": {"id": "thr_123"}}},
        {"id": 3, "result": {"turn": {"id": "turn_1"}}},
        {"method": "item/completed", "params": {
            "threadId": "thr_123", "turnId": "turn_1", "completedAtMs": 1,
            "item": {"id": "msg_1", "type": "agentMessage", "text": json.dumps(
                _managed_result({}),
            )},
        }},
        {"method": "turn/completed", "params": {
            "threadId": "thr_123",
            "turn": {"id": "turn_1", "status": "completed", "items": []},
        }},
    ])
    adapter = CodexWorkUnitAdapter(
        engine,
        CodexAppServer(cwd=tmp_path, process_factory=lambda *_args, **_kwargs: process),
        owner="codex",
    )

    result = adapter.run_session(run.run_id, max_units=5)

    assert result.decision == "retry"
    assert len(result.dispatched) == 1
    assert result.dispatched[0].submission.attempt_status == "rejected"
    assert engine.status(run.run_id)["step_id"] == "preflight"


def test_managed_session_retries_core_retry_unit_after_process_restart(tmp_path):
    from pactkit.workflow_engine import WorkflowEngine
    from pactkit_codex.app_server import CodexAppServer
    from pactkit_codex.work_unit_adapter import CodexWorkUnitAdapter

    config = tmp_path / ".codex/pactkit.yaml"
    config.parent.mkdir(parents=True)
    config.write_text("developer: test\n", encoding="utf-8")
    (tmp_path / "docs/product/stories").mkdir(parents=True)
    (tmp_path / "docs/architecture/graphs").mkdir(parents=True)
    engine = WorkflowEngine(tmp_path)
    run = engine.start("project-plan", goal="plan")
    old = engine.acquire(run.run_id, owner="codex", idempotency_key="old")
    engine.reject(old.unit_id, owner="codex", reason_code="host_restart")
    process = _FakeProcess([
        {"id": 1, "result": {}},
        {"id": 2, "result": {"thread": {"id": "thr_123"}}},
        {"id": 3, "result": {"turn": {"id": "turn_1"}}},
        {"method": "item/completed", "params": {
            "threadId": "thr_123", "turnId": "turn_1", "completedAtMs": 1,
            "item": {"id": "msg_1", "type": "agentMessage", "text": json.dumps(
                _managed_result({"guard": "pass"}),
            )},
        }},
        {"method": "turn/completed", "params": {
            "threadId": "thr_123",
            "turn": {"id": "turn_1", "status": "completed", "items": []},
        }},
    ])
    adapter = CodexWorkUnitAdapter(
        engine,
        CodexAppServer(cwd=tmp_path, process_factory=lambda *_args, **_kwargs: process),
        owner="codex",
    )

    result = adapter.run_session(run.run_id, max_units=1)

    assert result.dispatched[0].unit.unit_id == old.unit_id
    assert result.dispatched[0].unit.version == old.version + 1
    assert engine.status(run.run_id)["step_id"] == "clarification"


def test_managed_session_default_idempotency_namespace_is_unique_per_invocation(
    tmp_path, monkeypatch,
):
    from pactkit.workflow_engine import WorkflowEngine
    from pactkit_codex.work_unit_adapter import CodexWorkUnitAdapter

    engine = WorkflowEngine(tmp_path)
    adapter = object.__new__(CodexWorkUnitAdapter)
    adapter.engine = engine
    adapter.owner = "codex"
    prefixes = iter(("invocation-one", "invocation-two"))
    monkeypatch.setattr(
        "pactkit_codex.work_unit_adapter.uuid.uuid4",
        lambda: type("Id", (), {"hex": next(prefixes)})(),
    )

    assert adapter._idempotency_namespace(None) == "codex-session:invocation-one"
    assert adapter._idempotency_namespace(None) == "codex-session:invocation-two"
    assert adapter._idempotency_namespace("caller-owned") == "caller-owned"


def test_managed_session_uses_core_finalizer_for_terminal_unit(tmp_path):
    from pactkit_codex.app_server import CodexAppServer
    from pactkit_codex.work_unit_adapter import CodexWorkUnitAdapter

    engine, run, story_id = _prepare_finalize_run(tmp_path)
    process = _FakeProcess([
        {"id": 1, "result": {}},
        {"id": 2, "result": {"thread": {"id": "thr_123"}}},
        {"id": 3, "result": {"turn": {"id": "turn_final"}}},
        {"method": "item/completed", "params": {
            "threadId": "thr_123", "turnId": "turn_final", "completedAtMs": 1,
            "item": {"id": "msg_final", "type": "agentMessage", "text": json.dumps(
                _managed_result(
                    {}, story_id=story_id, title="Managed Plan",
                    tasks=["Implement managed loop"],
                ),
            )},
        }},
        {"method": "turn/completed", "params": {
            "threadId": "thr_123",
            "turn": {"id": "turn_final", "status": "completed", "items": []},
        }},
    ])
    adapter = CodexWorkUnitAdapter(
        engine,
        CodexAppServer(cwd=tmp_path, process_factory=lambda *_args, **_kwargs: process),
        owner="codex",
    )

    result = adapter.run_session(run.run_id, max_units=2)

    assert result.decision == "done"
    assert len(result.dispatched) == 1
    assert result.dispatched[0].unit.step_id == "finalize_plan"
    assert engine.status(run.run_id)["status"] == "completed"
    assert (tmp_path / f"docs/product/stories/{story_id}.yaml").is_file()
    assert (tmp_path / "docs/product/sprint_board.md").is_file()
    assert (tmp_path / ".pactkit/context.md").is_file()
    journal = json.loads(
        (tmp_path / f".pactkit/finalize/{run.run_id}.json").read_text(encoding="utf-8"),
    )
    final_unit = result.dispatched[0].unit
    assert journal["idempotency_key"] == f"{final_unit.unit_id}-v{final_unit.version}"


def test_finalize_prompt_reserves_governance_writes_for_core(tmp_path):
    from pactkit_codex.work_unit_adapter import CodexWorkUnitAdapter

    engine, run, _story_id = _prepare_finalize_run(tmp_path)
    unit = engine.acquire(run.run_id, owner="codex", idempotency_key="final")

    prompt = CodexWorkUnitAdapter._prompt(unit)

    assert "do not invoke finalize-plan" in prompt
    assert "return non-empty story_id, title, and tasks" in prompt


def test_runner_run_command_persists_thread_for_cross_process_resume(
    tmp_path, capsys, monkeypatch,
):
    from pactkit.workflow_engine import WorkflowEngine
    from pactkit_codex.app_server import CodexAppServer
    from pactkit_codex.runner import main
    from pactkit_codex.work_unit_adapter import CodexWorkUnitAdapter

    config = tmp_path / ".codex/pactkit.yaml"
    config.parent.mkdir(parents=True)
    config.write_text("developer: test\n", encoding="utf-8")
    (tmp_path / "docs/product/stories").mkdir(parents=True)
    (tmp_path / "docs/architecture/graphs").mkdir(parents=True)
    engine = WorkflowEngine(tmp_path)
    run = engine.start("project-plan", goal="plan")
    first_process = _FakeProcess([
        {"id": 1, "result": {}},
        {"id": 2, "result": {"thread": {"id": "thr_saved"}}},
        {"id": 3, "result": {"turn": {"id": "turn_1"}}},
        {"method": "item/completed", "params": {
            "threadId": "thr_saved", "turnId": "turn_1", "completedAtMs": 1,
            "item": {"id": "msg_1", "type": "agentMessage", "text": json.dumps(
                _managed_result({"guard": "pass"}),
            )},
        }},
        {"method": "turn/completed", "params": {
            "threadId": "thr_saved",
            "turn": {"id": "turn_1", "status": "completed", "items": []},
        }},
    ])
    processes = [first_process]

    def adapter_factory(root, owner):
        return CodexWorkUnitAdapter(
            WorkflowEngine(root),
            CodexAppServer(cwd=root, process_factory=lambda *_args, **_kwargs: processes.pop(0)),
            owner=owner,
        )

    monkeypatch.chdir(tmp_path)
    capsys.readouterr()  # discard fixture setup diagnostics from Core
    assert main([
        "run", run.run_id, "--owner", "codex", "--max-units", "1",
    ], adapter_factory=adapter_factory) == 0
    state_path = tmp_path / f".pactkit/codex-sessions/{run.run_id}.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert state == {"run_id": run.run_id, "thread_id": "thr_saved"}
    assert state_path.stat().st_mode & 0o777 == 0o600
    first_output = capsys.readouterr()
    assert json.loads(first_output.out)["decision"] == "unit_limit"
    assert "Wrote" not in first_output.out

    second_process = _FakeProcess([
        {"id": 1, "result": {}},
        {"id": 2, "result": {"thread": {"id": "thr_saved"}}},
        {"id": 3, "result": {"turn": {"id": "turn_2"}}},
        {"method": "item/completed", "params": {
            "threadId": "thr_saved", "turnId": "turn_2", "completedAtMs": 2,
            "item": {"id": "msg_2", "type": "agentMessage", "text": json.dumps(
                _managed_result({"clarification_resolved": True}),
            )},
        }},
        {"method": "turn/completed", "params": {
            "threadId": "thr_saved",
            "turn": {"id": "turn_2", "status": "completed", "items": []},
        }},
    ])
    processes.append(second_process)
    assert main([
        "run", run.run_id, "--owner", "codex", "--max-units", "1",
    ], adapter_factory=adapter_factory) == 0
    sent = [json.loads(line) for line in second_process.stdin.getvalue().splitlines()]
    assert any(item["method"] == "thread/resume" for item in sent)
    assert not any(item["method"] == "thread/start" for item in sent)
    second_output = capsys.readouterr()
    assert json.loads(second_output.out)["decision"] == "unit_limit"


def test_adapter_records_host_error_attempt_when_app_server_fails_after_acquire(tmp_path):
    from pactkit.workflow_engine import WorkflowEngine
    from pactkit_codex.app_server import AppServerError, CodexAppServer
    from pactkit_codex.work_unit_adapter import CodexWorkUnitAdapter

    config = tmp_path / ".codex/pactkit.yaml"
    config.parent.mkdir(parents=True)
    config.write_text("developer: test\n", encoding="utf-8")
    (tmp_path / "docs/product/stories").mkdir(parents=True)
    (tmp_path / "docs/architecture/graphs").mkdir(parents=True)
    engine = WorkflowEngine(tmp_path)
    run = engine.start("project-plan", goal="plan")
    process = _FakeProcess([
        {"id": 1, "result": {}},
        {"id": 2, "error": {"code": -1, "message": "thread failed"}},
    ])
    adapter = CodexWorkUnitAdapter(
        engine,
        CodexAppServer(cwd=tmp_path, process_factory=lambda *_args, **_kwargs: process),
        owner="codex",
    )

    with pytest.raises(AppServerError, match="thread failed"):
        adapter.execute(run.run_id, idempotency_key="acquire-1")

    attempt = engine._read(run.run_id)["attempts"][-1]
    assert attempt["status"] == "host_error"
    assert attempt["reason_code"] == "app_server_protocol_error"
    assert attempt["decision"] == "retry"
    assert attempt["adapter_version"]
    assert engine._read(run.run_id)["units"][attempt["unit_id"]]["state"] == "retry"


def test_managed_session_failed_turn_has_reason_and_one_terminal_attempt(tmp_path):
    from pactkit.workflow_engine import WorkflowEngine
    from pactkit_codex.app_server import CodexAppServer
    from pactkit_codex.work_unit_adapter import CodexWorkUnitAdapter

    config = tmp_path / ".codex/pactkit.yaml"
    config.parent.mkdir(parents=True)
    config.write_text("developer: test\n", encoding="utf-8")
    (tmp_path / "docs/product/stories").mkdir(parents=True)
    (tmp_path / "docs/architecture/graphs").mkdir(parents=True)
    engine = WorkflowEngine(tmp_path)
    run = engine.start("project-plan", goal="plan")
    process = _FakeProcess([
        {"id": 1, "result": {}},
        {"id": 2, "result": {"thread": {"id": "thr_123"}}},
        {"id": 3, "result": {"turn": {"id": "turn_failed"}}},
        {"method": "turn/completed", "params": {
            "threadId": "thr_123",
            "turn": {"id": "turn_failed", "status": "failed", "items": []},
        }},
    ])
    adapter = CodexWorkUnitAdapter(
        engine,
        CodexAppServer(cwd=tmp_path, process_factory=lambda *_args, **_kwargs: process),
        owner="codex",
    )

    result = adapter.run_session(run.run_id, max_units=1)

    assert result.decision == "retry"
    attempts = engine._read(run.run_id)["attempts"]
    terminal = [item for item in attempts if item["turn_ref"] is not None]
    assert len(terminal) == 1
    assert terminal[0]["status"] == "host_error"
    assert terminal[0]["reason_code"] == "turn_failed"


def test_adapter_records_awaiting_approval_as_recoverable_attempt(tmp_path):
    from pactkit.workflow_engine import WorkflowEngine
    from pactkit_codex.app_server import AppServerApprovalRequired, CodexAppServer
    from pactkit_codex.work_unit_adapter import CodexWorkUnitAdapter

    config = tmp_path / ".codex/pactkit.yaml"
    config.parent.mkdir(parents=True)
    config.write_text("developer: test\n", encoding="utf-8")
    (tmp_path / "docs/product/stories").mkdir(parents=True)
    (tmp_path / "docs/architecture/graphs").mkdir(parents=True)
    engine = WorkflowEngine(tmp_path)
    run = engine.start("project-plan", goal="plan")
    process = _FakeProcess([
        {"id": 1, "result": {}},
        {"id": 2, "result": {"thread": {"id": "thr_123"}}},
        {"id": 3, "result": {"turn": {"id": "turn_456"}}},
        {
            "id": 4,
            "method": "item/commandExecution/requestApproval",
            "params": {"threadId": "thr_123", "turnId": "turn_456"},
        },
    ])
    adapter = CodexWorkUnitAdapter(
        engine,
        CodexAppServer(cwd=tmp_path, process_factory=lambda *_args, **_kwargs: process),
        owner="codex",
    )

    with pytest.raises(AppServerApprovalRequired, match="approval_required"):
        adapter.execute(run.run_id, idempotency_key="acquire-1")

    attempt = engine._read(run.run_id)["attempts"][-1]
    assert attempt["status"] == "awaiting_approval"
    assert attempt["reason_code"] == "app_server_approval_required"
    assert attempt["decision"] == "await_approval"
    assert engine._read(run.run_id)["units"][attempt["unit_id"]]["state"] == "retry"


def test_managed_session_pauses_before_manual_operation_without_starting_turn(tmp_path):
    from pactkit.workflow_engine import EvidenceReceipt, WorkflowEngine
    from pactkit_codex.app_server import CodexAppServer
    from pactkit_codex.work_unit_adapter import CodexWorkUnitAdapter

    engine = WorkflowEngine(tmp_path)
    run = engine.start("project-pr", goal="open PR")
    for step, claims in (("preflight", {"ready": True}),):
        unit = engine.acquire(run.run_id, owner="codex", idempotency_key=step)
        assert engine.submit(
            unit.unit_id, EvidenceReceipt.for_files(
                unit, owner="codex", root=tmp_path, files=[], claims=claims,
            ), owner="codex", idempotency_key=f"{step}-submit",
        ).attempt_status == "succeeded"
    process = _FakeProcess([
        {"id": 1, "result": {}},
        {"id": 2, "result": {"thread": {"id": "thr_manual"}}},
    ])
    adapter = CodexWorkUnitAdapter(
        engine, CodexAppServer(cwd=tmp_path, process_factory=lambda *_a, **_k: process),
        owner="codex",
    )

    result = adapter.run_session(run.run_id, max_units=1)

    assert result.decision == "await_user"
    assert result.dispatched[0].terminal_status == "awaiting_approval"
    sent = [json.loads(line) for line in process.stdin.getvalue().splitlines()]
    assert not any(item.get("method") == "turn/start" for item in sent)
    state = engine._read(run.run_id)
    assert next(iter(state["units"].values()))["state"] == "succeeded"
    publish = [item for item in state["units"].values() if item["step_id"] == "publish"][0]
    assert publish["state"] == "retry"


def test_managed_session_resumes_authorized_manual_unit_on_same_thread(tmp_path):
    from pactkit.workflow_engine import EvidenceReceipt, WorkflowEngine
    from pactkit_codex.app_server import CodexAppServer
    from pactkit_codex.work_unit_adapter import CodexWorkUnitAdapter

    engine = WorkflowEngine(tmp_path)
    run = engine.start("project-pr", goal="open PR")
    unit = engine.acquire(run.run_id, owner="codex", idempotency_key="preflight")
    assert engine.submit(
        unit.unit_id, EvidenceReceipt.for_files(
            unit, owner="codex", root=tmp_path, files=[], claims={"ready": True},
        ), owner="codex", idempotency_key="preflight-submit",
    ).attempt_status == "succeeded"
    paused_process = _FakeProcess([
        {"id": 1, "result": {}},
        {"id": 2, "result": {"thread": {"id": "thr_manual"}}},
    ])
    paused = CodexWorkUnitAdapter(
        engine, CodexAppServer(cwd=tmp_path, process_factory=lambda *_a, **_k: paused_process),
        owner="codex",
    ).run_session(run.run_id, max_units=1)
    old = paused.dispatched[0].unit

    resumed_process = _FakeProcess([
        {"id": 1, "result": {}},
        {"id": 2, "result": {"thread": {"id": "thr_manual"}}},
        {"id": 3, "result": {"turn": {"id": "turn_publish"}}},
        {"method": "item/completed", "params": {
            "threadId": "thr_manual", "turnId": "turn_publish", "completedAtMs": 1,
            "item": {"id": "msg", "type": "agentMessage", "text": json.dumps(
                _managed_result({
                    "branch": "feature/test",
                    "pull_request": {"mode": "not_required", "reason": "local test"},
                }),
            )},
        }},
        {"method": "turn/completed", "params": {
            "threadId": "thr_manual",
            "turn": {"id": "turn_publish", "status": "completed", "items": []},
        }},
    ])
    resumed = CodexWorkUnitAdapter(
        engine, CodexAppServer(cwd=tmp_path, process_factory=lambda *_a, **_k: resumed_process),
        owner="codex",
    ).run_session(
        run.run_id, thread_id="thr_manual", max_units=1,
        authorized_operations=frozenset({"push", "pull_request"}),
    )

    assert resumed.decision == "unit_limit"
    assert resumed.dispatched[0].unit.unit_id == old.unit_id
    assert resumed.dispatched[0].unit.version == old.version + 1
    sent = [json.loads(line) for line in resumed_process.stdin.getvalue().splitlines()]
    assert any(item.get("method") == "thread/resume" for item in sent)
    assert any(item.get("method") == "turn/start" for item in sent)


def test_managed_session_returns_retry_for_out_of_scope_model_evidence(tmp_path):
    from pactkit.workflow_engine import WorkflowEngine
    from pactkit_codex.app_server import CodexAppServer
    from pactkit_codex.work_unit_adapter import CodexWorkUnitAdapter

    engine = WorkflowEngine(tmp_path)
    run = engine.start("project-debug", goal="diagnose")
    process = _FakeProcess([
        {"id": 1, "result": {}},
        {"id": 2, "result": {"thread": {"id": "thr_retry"}}},
        {"id": 3, "result": {"turn": {"id": "turn_bad"}}},
        {"method": "item/completed", "params": {
            "threadId": "thr_retry", "turnId": "turn_bad",
            "item": {"id": "msg", "type": "agentMessage", "text": json.dumps(
                _managed_result({"ready": True}, evidence_files=["/outside-repo.md"]),
            )},
        }},
        {"method": "turn/completed", "params": {
            "threadId": "thr_retry",
            "turn": {"id": "turn_bad", "status": "completed", "items": []},
        }},
    ])

    result = CodexWorkUnitAdapter(
        engine,
        CodexAppServer(cwd=tmp_path, process_factory=lambda *_a, **_k: process),
        owner="codex",
    ).run_session(run.run_id, max_units=1)

    assert result.decision == "retry"
    assert result.dispatched[0].terminal_status == "malformed_result"
    state = engine._read(run.run_id)
    assert next(iter(state["units"].values()))["state"] == "retry"
    assert state["attempts"][-1]["reason_code"] == "structured_result_invalid"


def test_runner_cli_executes_the_production_adapter_path(tmp_path, capsys, monkeypatch):
    from pactkit.workflow_engine import WorkflowEngine
    from pactkit_codex.app_server import CodexAppServer
    from pactkit_codex.runner import main
    from pactkit_codex.work_unit_adapter import CodexWorkUnitAdapter

    config = tmp_path / ".codex/pactkit.yaml"
    config.parent.mkdir(parents=True)
    config.write_text("developer: test\n", encoding="utf-8")
    (tmp_path / "docs/product/stories").mkdir(parents=True)
    (tmp_path / "docs/architecture/graphs").mkdir(parents=True)
    engine = WorkflowEngine(tmp_path)
    run = engine.start("project-plan", goal="plan")
    process = _FakeProcess([
        {"id": 1, "result": {}},
        {"id": 2, "result": {"thread": {"id": "thr_123"}}},
        {"id": 3, "result": {"turn": {"id": "turn_456"}}},
        {"method": "turn/completed", "params": {
            "turn": {"id": "turn_456", "status": "completed"},
        }},
    ])

    def adapter_factory(root, owner):
        return CodexWorkUnitAdapter(
            WorkflowEngine(root),
            CodexAppServer(cwd=root, process_factory=lambda *_args, **_kwargs: process),
            owner=owner,
        )

    receipt_path = tmp_path / "receipt.json"
    receipt_path.write_text(json.dumps({"claims": {"guard": "pass"}}), encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    assert main([
        "execute", run.run_id, "--owner", "codex",
        "--idempotency-key", "acquire-1", "--receipt", "@receipt.json",
    ], adapter_factory=adapter_factory) == 0

    output = capsys.readouterr().out
    result = json.loads(output[output.index("{"):])
    assert result["submission"]["attempt_status"] == "succeeded"
    assert engine.status(run.run_id)["step_id"] == "clarification"


def test_runner_cli_returns_nonzero_after_app_server_failure(tmp_path, capsys, monkeypatch):
    from pactkit.workflow_engine import WorkflowEngine
    from pactkit_codex.app_server import CodexAppServer
    from pactkit_codex.runner import main
    from pactkit_codex.work_unit_adapter import CodexWorkUnitAdapter

    config = tmp_path / ".codex/pactkit.yaml"
    config.parent.mkdir(parents=True)
    config.write_text("developer: test\n", encoding="utf-8")
    (tmp_path / "docs/product/stories").mkdir(parents=True)
    (tmp_path / "docs/architecture/graphs").mkdir(parents=True)
    engine = WorkflowEngine(tmp_path)
    run = engine.start("project-plan", goal="plan")
    process = _FakeProcess([
        {"id": 1, "result": {}},
        {"id": 2, "error": {"code": -1, "message": "thread failed"}},
    ])

    def adapter_factory(root, owner):
        return CodexWorkUnitAdapter(
            WorkflowEngine(root),
            CodexAppServer(cwd=root, process_factory=lambda *_args, **_kwargs: process),
            owner=owner,
        )

    monkeypatch.chdir(tmp_path)
    assert main([
        "execute", run.run_id, "--owner", "codex", "--idempotency-key", "acquire-1",
        "--receipt", "{}",
    ], adapter_factory=adapter_factory) == 1
    assert "Codex WorkUnit error: thread failed" in capsys.readouterr().out
    assert engine._read(run.run_id)["attempts"][-1]["status"] == "host_error"


def test_runner_requires_candidate_receipt_before_leasing_work_unit(tmp_path, monkeypatch):
    from pactkit.workflow_engine import WorkflowEngine
    from pactkit_codex.runner import main

    _ = WorkflowEngine(tmp_path).start("project-plan", goal="plan")
    monkeypatch.chdir(tmp_path)

    with pytest.raises(SystemExit) as exc_info:
        main([
            "execute", _.run_id, "--owner", "codex", "--idempotency-key", "acquire-1",
        ])

    assert exc_info.value.code == 2


def test_runner_returns_nonzero_when_core_rejects_candidate_receipt(tmp_path, capsys, monkeypatch):
    from pactkit.workflow_engine import WorkflowEngine
    from pactkit_codex.app_server import CodexAppServer
    from pactkit_codex.runner import main
    from pactkit_codex.work_unit_adapter import CodexWorkUnitAdapter

    config = tmp_path / ".codex/pactkit.yaml"
    config.parent.mkdir(parents=True)
    config.write_text("developer: test\n", encoding="utf-8")
    (tmp_path / "docs/product/stories").mkdir(parents=True)
    (tmp_path / "docs/architecture/graphs").mkdir(parents=True)
    engine = WorkflowEngine(tmp_path)
    run = engine.start("project-plan", goal="plan")
    process = _FakeProcess([
        {"id": 1, "result": {}},
        {"id": 2, "result": {"thread": {"id": "thr_123"}}},
        {"id": 3, "result": {"turn": {"id": "turn_456"}}},
        {"method": "turn/completed", "params": {
            "turn": {"id": "turn_456", "status": "completed"},
        }},
    ])

    def adapter_factory(root, owner):
        return CodexWorkUnitAdapter(
            WorkflowEngine(root),
            CodexAppServer(cwd=root, process_factory=lambda *_args, **_kwargs: process),
            owner=owner,
        )

    receipt_path = tmp_path / "receipt.json"
    receipt_path.write_text(json.dumps({"claims": {}}), encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    assert main([
        "execute", run.run_id, "--owner", "codex",
        "--idempotency-key", "acquire-1", "--receipt", "@receipt.json",
    ], adapter_factory=adapter_factory) == 1

    output = capsys.readouterr().out
    result = json.loads(output[output.index("{"):])
    assert result["submission"]["attempt_status"] == "rejected"
    assert result["submission"]["reason_code"] == "validator_failed"
    assert engine._read(run.run_id)["units"][result["unit"]["unit_id"]]["state"] == "retry"


def test_runner_calculates_candidate_fingerprints_from_evidence_files(tmp_path):
    from pactkit.workflow_engine import WorkflowEngine
    from pactkit_codex.runner import _receipt_from_template

    evidence = tmp_path / "docs/specs/STORY-slim-999.md"
    evidence.parent.mkdir(parents=True)
    evidence.write_text("# Evidence\n", encoding="utf-8")
    engine = WorkflowEngine(tmp_path)
    run = engine.start("project-plan", goal="plan")
    unit = engine.acquire(run.run_id, owner="codex", idempotency_key="acquire")

    receipt = _receipt_from_template(
        {"claims": {"guard": "pass"}, "evidence_files": ["docs/specs/STORY-slim-999.md"]},
        unit,
        owner="codex",
        root=tmp_path,
    )

    assert receipt.file_fingerprints == {
        "docs/specs/STORY-slim-999.md": __import__("hashlib").sha256(evidence.read_bytes()).hexdigest(),
    }


def test_runner_releases_unit_when_receipt_template_cannot_be_bound(tmp_path, capsys, monkeypatch):
    from pactkit.workflow_engine import WorkflowEngine
    from pactkit_codex.app_server import CodexAppServer
    from pactkit_codex.runner import main
    from pactkit_codex.work_unit_adapter import CodexWorkUnitAdapter

    config = tmp_path / ".codex/pactkit.yaml"
    config.parent.mkdir(parents=True)
    config.write_text("developer: test\n", encoding="utf-8")
    (tmp_path / "docs/product/stories").mkdir(parents=True)
    (tmp_path / "docs/architecture/graphs").mkdir(parents=True)
    engine = WorkflowEngine(tmp_path)
    run = engine.start("project-plan", goal="plan")
    process = _FakeProcess([
        {"id": 1, "result": {}},
        {"id": 2, "result": {"thread": {"id": "thr_123"}}},
        {"id": 3, "result": {"turn": {"id": "turn_456"}}},
        {"method": "turn/completed", "params": {
            "turn": {"id": "turn_456", "status": "completed"},
        }},
    ])

    def adapter_factory(root, owner):
        return CodexWorkUnitAdapter(
            WorkflowEngine(root),
            CodexAppServer(cwd=root, process_factory=lambda *_args, **_kwargs: process),
            owner=owner,
        )

    receipt_path = tmp_path / "receipt.json"
    receipt_path.write_text(json.dumps({"evidence_files": ["/outside-repo.md"]}), encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    assert main([
        "execute", run.run_id, "--owner", "codex",
        "--idempotency-key", "acquire-1", "--receipt", "@receipt.json",
    ], adapter_factory=adapter_factory) == 1

    attempt = engine._read(run.run_id)["attempts"][-1]
    assert attempt["status"] == "malformed_result"
    assert attempt["reason_code"] == "receipt_construction_failed"
    assert engine._read(run.run_id)["units"][attempt["unit_id"]]["state"] == "retry"
    assert "Codex WorkUnit error: invalid_evidence_path" in capsys.readouterr().out
    attempts = engine._read(run.run_id)["attempts"]
    assert [attempt["status"] for attempt in attempts] == ["malformed_result"]


@pytest.mark.parametrize(
    "receipt_factory",
    [
        lambda _unit, _terminal: object(),
        lambda _unit, _terminal: (_ for _ in ()).throw(RuntimeError("factory failed")),
    ],
)
def test_adapter_releases_unit_when_receipt_factory_cannot_construct_candidate(
    tmp_path, receipt_factory,
):
    from pactkit.workflow_engine import WorkflowEngine
    from pactkit_codex.app_server import CodexAppServer
    from pactkit_codex.work_unit_adapter import CodexWorkUnitAdapter

    config = tmp_path / ".codex/pactkit.yaml"
    config.parent.mkdir(parents=True)
    config.write_text("developer: test\n", encoding="utf-8")
    (tmp_path / "docs/product/stories").mkdir(parents=True)
    (tmp_path / "docs/architecture/graphs").mkdir(parents=True)
    engine = WorkflowEngine(tmp_path)
    run = engine.start("project-plan", goal="plan")
    process = _FakeProcess([
        {"id": 1, "result": {}},
        {"id": 2, "result": {"thread": {"id": "thr_123"}}},
        {"id": 3, "result": {"turn": {"id": "turn_456"}}},
        {"method": "turn/completed", "params": {
            "turn": {"id": "turn_456", "status": "completed"},
        }},
    ])
    adapter = CodexWorkUnitAdapter(
        engine,
        CodexAppServer(cwd=tmp_path, process_factory=lambda *_args, **_kwargs: process),
        owner="codex",
    )

    with pytest.raises((RuntimeError, TypeError)):
        adapter.execute(
            run.run_id, idempotency_key="acquire-1",
            receipt_factory=receipt_factory,
        )

    attempts = engine._read(run.run_id)["attempts"]
    assert [attempt["status"] for attempt in attempts] == ["malformed_result"]
    assert attempts[0]["reason_code"] == "receipt_construction_failed"
    assert engine._read(run.run_id)["units"][attempts[0]["unit_id"]]["state"] == "retry"


@pytest.mark.parametrize(
    ("receipt_arg", "expected_error"),
    [
        ("{not-json", "receipt_template_invalid_json"),
        ("@missing-receipt.json", "receipt_template_unavailable"),
    ],
)
def test_runner_records_malformed_attempt_for_unreadable_or_invalid_receipt_template(
    tmp_path, capsys, monkeypatch, receipt_arg, expected_error,
):
    from pactkit.workflow_engine import WorkflowEngine
    from pactkit_codex.app_server import CodexAppServer
    from pactkit_codex.runner import main
    from pactkit_codex.work_unit_adapter import CodexWorkUnitAdapter

    config = tmp_path / ".codex/pactkit.yaml"
    config.parent.mkdir(parents=True)
    config.write_text("developer: test\n", encoding="utf-8")
    (tmp_path / "docs/product/stories").mkdir(parents=True)
    (tmp_path / "docs/architecture/graphs").mkdir(parents=True)
    engine = WorkflowEngine(tmp_path)
    run = engine.start("project-plan", goal="plan")
    process = _FakeProcess([
        {"id": 1, "result": {}},
        {"id": 2, "result": {"thread": {"id": "thr_123"}}},
        {"id": 3, "result": {"turn": {"id": "turn_456"}}},
        {"method": "turn/completed", "params": {
            "turn": {"id": "turn_456", "status": "completed"},
        }},
    ])

    def adapter_factory(root, owner):
        return CodexWorkUnitAdapter(
            WorkflowEngine(root),
            CodexAppServer(cwd=root, process_factory=lambda *_args, **_kwargs: process),
            owner=owner,
        )

    monkeypatch.chdir(tmp_path)
    assert main([
        "execute", run.run_id, "--owner", "codex",
        "--idempotency-key", "acquire-1", "--receipt", receipt_arg,
    ], adapter_factory=adapter_factory) == 1

    attempt = engine._read(run.run_id)["attempts"][-1]
    assert attempt["status"] == "malformed_result"
    assert attempt["reason_code"] == "receipt_construction_failed"
    assert engine._read(run.run_id)["units"][attempt["unit_id"]]["state"] == "retry"
    output = capsys.readouterr().out
    assert f"Codex WorkUnit error: {expected_error}" in output
    assert str(tmp_path) not in output
