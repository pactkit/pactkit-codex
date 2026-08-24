"""Thin JSON-RPC bridge for the official Codex App Server.

The bridge owns only transport and host lifecycle references.  PactKit Core
remains the authority for WorkUnit scheduling, receipt validation, and workflow
completion.  A protocol-level unit test is deliberately not host E2E evidence.
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable


class AppServerError(RuntimeError):
    """The local App Server process or stream is unavailable."""


class AppServerProtocolError(AppServerError):
    """The App Server returned malformed or error JSON-RPC output."""


class AppServerApprovalRequired(AppServerError):
    """The App Server requires a human approval before this turn can continue."""


@dataclass(frozen=True)
class StartedTurn:
    thread_id: str
    turn_id: str


@dataclass(frozen=True)
class TurnTerminal:
    thread_id: str | None
    turn_id: str
    status: str
    output_text: str | None = None


ProcessFactory = Callable[..., Any]


def app_server_capability() -> dict[str, object]:
    """Describe the strongest lifecycle mode verified against Codex App Server."""
    return {
        "protocol_version": 1,
        "verification_source": "official_app_server_live_workunit_e2e",
        "structured_results": True,
        "tool_execution": True,
        # The bridge deliberately does not answer server-initiated approval
        # requests. Advertising approval here would let Core schedule work on
        # a capability that cannot actually complete an approval handshake.
        "approval": False,
        "lifecycle_events": True,
        "thread_resume": True,
        "turn_steer": True,
        "background_execution": False,
        "cancellation": True,
        "e2e_validated": True,
        "execution_mode": "resumable",
    }


class CodexAppServer:
    """One stdio connection to ``codex app-server``."""

    def __init__(
        self, *, cwd: Path, command: tuple[str, ...] = ("codex", "app-server"),
        process_factory: ProcessFactory = subprocess.Popen,
    ) -> None:
        self.cwd = Path(cwd).resolve()
        self.command = command
        self.process_factory = process_factory
        self.process: Any | None = None
        self._next_id = 1

    def connect(self) -> None:
        if self.process is not None:
            raise AppServerError("app_server_already_connected")
        try:
            self.process = self.process_factory(
                self.command,
                cwd=self.cwd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
            )
        except OSError as exc:
            raise AppServerError("app_server_unavailable") from exc
        self._request(
            "initialize",
            {
                "clientInfo": {
                    "name": "pactkit_codex",
                    "title": "PactKit Codex Adapter",
                    "version": "1",
                },
                "capabilities": {"experimentalApi": False},
            },
        )
        # The App Server protocol defines ``initialized`` as a parameterless
        # notification. Sending an empty params object is still a schema
        # violation under strict JSON-RPC validation.
        self._notify("initialized")

    def start_thread(self, *, model: str | None = None) -> str:
        params = {"cwd": str(self.cwd)}
        if model is not None:
            params["model"] = model
        result = self._request("thread/start", params)
        return self._thread_id(result)

    def resume_thread(self, thread_id: str) -> str:
        result = self._request("thread/resume", {"threadId": thread_id})
        resumed = self._thread_id(result)
        if resumed != thread_id:
            raise AppServerProtocolError("thread_resume_id_mismatch")
        return resumed

    def start_turn(
        self, thread_id: str, prompt: str, *,
        output_schema: dict[str, object] | None = None,
    ) -> StartedTurn:
        if not isinstance(prompt, str) or not prompt.strip():
            raise AppServerProtocolError("invalid_turn_input")
        params: dict[str, object] = {
            "threadId": thread_id,
            "input": [{"type": "text", "text": prompt}],
            "cwd": str(self.cwd),
        }
        if output_schema is not None:
            if not isinstance(output_schema, dict):
                raise AppServerProtocolError("invalid_output_schema")
            params["outputSchema"] = output_schema
        result = self._request("turn/start", params)
        turn = result.get("turn") if isinstance(result, dict) else None
        turn_id = turn.get("id") if isinstance(turn, dict) else None
        if not isinstance(turn_id, str) or not turn_id:
            raise AppServerProtocolError("invalid_turn_start_result")
        return StartedTurn(thread_id=thread_id, turn_id=turn_id)

    def steer_turn(self, thread_id: str, expected_turn_id: str, prompt: str) -> str:
        if not isinstance(expected_turn_id, str) or not expected_turn_id:
            raise AppServerProtocolError("invalid_expected_turn_id")
        result = self._request(
            "turn/steer",
            {
                "threadId": thread_id,
                "expectedTurnId": expected_turn_id,
                "input": [{"type": "text", "text": prompt}],
            },
        )
        turn_id = result.get("turnId") if isinstance(result, dict) else None
        if not isinstance(turn_id, str) or not turn_id:
            raise AppServerProtocolError("invalid_turn_steer_result")
        return turn_id

    def interrupt_turn(self, thread_id: str, turn_id: str) -> None:
        self._request("turn/interrupt", {"threadId": thread_id, "turnId": turn_id})

    def wait_for_turn(
        self, turn_id: str, *, thread_id: str | None = None,
        require_output: bool = False,
    ) -> TurnTerminal:
        output_text: str | None = None
        while True:
            message = self._read_message()
            # App Server approval callbacks are JSON-RPC requests rather than
            # notifications. This non-interactive bridge cannot truthfully
            # answer on a user's behalf, so surface a bounded state to Core
            # instead of silently consuming the request and hanging forever.
            if message.get("id") is not None and isinstance(message.get("method"), str):
                method = message["method"]
                if "requestApproval" in method or method == "applyPatchApproval":
                    raise AppServerApprovalRequired("app_server_approval_required")
            if message.get("method") == "item/completed":
                params = message.get("params")
                if not isinstance(params, dict):
                    continue
                if params.get("turnId") != turn_id:
                    continue
                if thread_id is not None and params.get("threadId") != thread_id:
                    continue
                item = params.get("item")
                if not isinstance(item, dict) or item.get("type") != "agentMessage":
                    continue
                text = item.get("text")
                if not isinstance(text, str) or not text.strip():
                    # App Server can emit an empty intermediate AgentMessage
                    # around tool calls. It is not the terminal structured
                    # result; absence is checked when the turn completes.
                    continue
                # Codex may emit structured progress messages before its final
                # response. The last completed AgentMessage for this exact
                # thread/turn is authoritative when turn/completed arrives.
                output_text = self._normalize_agent_output(text)
                continue
            if message.get("method") != "turn/completed":
                continue
            params = message.get("params")
            turn = params.get("turn") if isinstance(params, dict) else None
            if not isinstance(turn, dict) or turn.get("id") != turn_id:
                continue
            event_thread = params.get("threadId")
            if thread_id is not None and event_thread != thread_id:
                continue
            status = turn.get("status")
            if not isinstance(status, str) or not status:
                raise AppServerProtocolError("invalid_turn_completed_event")
            if require_output and status == "completed" and output_text is None:
                raise AppServerProtocolError("missing_structured_result")
            return TurnTerminal(
                thread_id=event_thread if isinstance(event_thread, str) else None,
                turn_id=turn_id,
                status=status,
                output_text=output_text,
            )

    @staticmethod
    def _normalize_agent_output(text: str) -> str:
        """Return one strict JSON object from a provider's agent message.

        Some OpenAI-compatible proxies concatenate successive structured
        outputs with newlines.  Accept that observed shape only when every
        non-empty line is independently a JSON object; arbitrary mixed prose
        or malformed JSON remains untouched and therefore fails closed in the
        adapter's structured-result parser.
        """
        try:
            value = json.loads(text)
        except json.JSONDecodeError:
            value = None
        if isinstance(value, dict):
            return text
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        if len(lines) < 2:
            return text
        try:
            values = [json.loads(line) for line in lines]
        except json.JSONDecodeError:
            return text
        if not all(isinstance(item, dict) for item in values):
            return text
        return lines[-1]

    def close(self) -> None:
        if self.process is None:
            return
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
        self.process = None

    def _request(self, method: str, params: dict[str, object]) -> dict[str, object]:
        request_id = self._next_id
        self._next_id += 1
        self._send({"method": method, "id": request_id, "params": params})
        while True:
            message = self._read_message()
            if message.get("id") != request_id:
                continue
            error = message.get("error")
            if isinstance(error, dict):
                detail = error.get("message")
                raise AppServerProtocolError(str(detail or "app_server_request_failed"))
            result = message.get("result")
            if not isinstance(result, dict):
                raise AppServerProtocolError("invalid_app_server_response")
            return result

    def _notify(self, method: str) -> None:
        self._send({"method": method})

    def _send(self, message: dict[str, object]) -> None:
        if self.process is None or not all(
            hasattr(self.process.stdin, attribute) for attribute in ("write", "flush")
        ):
            raise AppServerError("app_server_not_connected")
        self.process.stdin.write(json.dumps(message, separators=(",", ":")) + "\n")
        self.process.stdin.flush()

    def _read_message(self) -> dict[str, object]:
        if self.process is None or not hasattr(self.process.stdout, "readline"):
            raise AppServerError("app_server_not_connected")
        line = self.process.stdout.readline()
        if not line:
            raise AppServerError("app_server_stream_closed")
        try:
            message = json.loads(line)
        except json.JSONDecodeError as exc:
            raise AppServerProtocolError("invalid_app_server_json") from exc
        if not isinstance(message, dict):
            raise AppServerProtocolError("invalid_app_server_message")
        return message

    @staticmethod
    def _thread_id(result: dict[str, object]) -> str:
        thread = result.get("thread")
        thread_id = thread.get("id") if isinstance(thread, dict) else None
        if not isinstance(thread_id, str) or not thread_id:
            raise AppServerProtocolError("invalid_thread_result")
        return thread_id
