import json
import os
import subprocess
import sys
import hashlib
from pathlib import Path


def _event(tmp_path, **overrides):
    value = {
        "cwd": str(tmp_path), "session_id": "session-1", "turn_id": "turn-1",
        "hook_event_name": "Stop", "stop_hook_active": False,
        "last_assistant_message": "progress only",
    }
    value.update(overrides)
    return value


def test_stop_handler_blocks_incomplete_run_and_allows_unmanaged_project(tmp_path, monkeypatch):
    from pactkit.continuation import ContinuationEngine
    from pactkit_codex.stop_hook import handle_stop
    monkeypatch.setenv("CODEX_HOME", str(tmp_path / "codex-home"))

    unmanaged = handle_stop(_event(tmp_path))
    assert unmanaged == {}

    engine = ContinuationEngine(tmp_path)
    state = engine.start("project-debug", evidence={"started": True})
    engine.bind_host_session(state["run_id"], session_id="session-1", turn_id="turn-1")

    result = handle_stop(_event(tmp_path))

    assert result["decision"] == "block"
    assert state["run_id"] in result["reason"]
    assert "hypotheses_tested" in result["reason"]
    assert engine.resolve_host_run(session_id="session-1")["run_id"] == state["run_id"]


def test_unique_active_fallback_is_bound_for_final_completed_stop(tmp_path, monkeypatch):
    from pactkit.continuation import ContinuationEngine
    from pactkit_codex.stop_hook import handle_stop

    monkeypatch.setenv("CODEX_HOME", str(tmp_path / "codex-home"))
    engine = ContinuationEngine(tmp_path)
    state = engine.start("project-debug", evidence={"started": True})
    assert handle_stop(_event(tmp_path, session_id="new-session"))["decision"] == "block"
    for step in ("hypotheses_tested", "root_cause_found"):
        engine.checkpoint(state["run_id"], step_id=step, evidence={"phase": "verified"})
    engine.checkpoint(
        state["run_id"], step_id="completed", status="completed",
        evidence={"root_cause": "cause", "evidence": ["proof"], "next_action": "done"},
    )

    assert handle_stop(_event(tmp_path, session_id="new-session", turn_id="turn-2")) == {}
    observed = json.loads(
        (tmp_path / "codex-home" / "pactkit-hook-state.json").read_text()
    )
    run_observation = observed["runs"][state["run_id"]]
    assert run_observation["block_observed"] is True
    assert run_observation["done_observed"] is True


def test_stop_handler_allows_completed_and_ignores_message_authority(tmp_path, monkeypatch):
    from pactkit.continuation import ContinuationEngine
    from pactkit_codex.stop_hook import handle_stop
    monkeypatch.setenv("CODEX_HOME", str(tmp_path / "codex-home"))

    engine = ContinuationEngine(tmp_path)
    state = engine.start("project-debug", evidence={"started": True})
    engine.bind_host_session(state["run_id"], session_id="session-1", turn_id="turn-1")
    for step in ("hypotheses_tested", "root_cause_found"):
        engine.checkpoint(state["run_id"], step_id=step, evidence={"phase": "verified"})
    engine.checkpoint(
        state["run_id"], step_id="completed", status="completed",
        evidence={"root_cause": "cause", "evidence": ["proof"], "next_action": "fix"},
    )

    result = handle_stop(_event(tmp_path, last_assistant_message="still unfinished"))

    assert result == {}


def test_stop_handler_returns_valid_diagnostic_for_ambiguous_runs(tmp_path, monkeypatch):
    from pactkit.continuation import ContinuationEngine
    from pactkit_codex.stop_hook import handle_stop
    monkeypatch.setenv("CODEX_HOME", str(tmp_path / "codex-home"))

    engine = ContinuationEngine(tmp_path)
    engine.start("project-debug", evidence={"started": True})
    engine.start("project-clarify", evidence={"started": True})

    result = handle_stop(_event(tmp_path, session_id="unknown"))

    assert result["decision"] == "block"
    assert "multiple_active_runs" in result["reason"]
    assert handle_stop(_event(
        tmp_path, session_id="unknown", stop_hook_active=True,
    )) == {}


def test_deployer_merges_owned_stop_hook_idempotently(tmp_path):
    from pactkit_codex.deployer import CodexDeployer

    hooks = tmp_path / "hooks.json"
    hooks.write_text(json.dumps({
        "description": "user hooks",
        "hooks": {"Stop": [{"hooks": [{"type": "command", "command": "user-stop"}]}]},
    }), encoding="utf-8")

    CodexDeployer.deploy_stop_hook(tmp_path)
    first = json.loads(hooks.read_text(encoding="utf-8"))
    CodexDeployer.deploy_stop_hook(tmp_path)
    second = json.loads(hooks.read_text(encoding="utf-8"))

    assert first == second
    commands = [item["hooks"][0]["command"] for item in second["hooks"]["Stop"]]
    assert "user-stop" in commands
    assert commands.count("pactkit-codex-stop-hook") == 1
    assert (tmp_path / "hooks" / "pactkit_stop.py").is_file()

    CodexDeployer.remove_stop_hook(tmp_path)
    removed = json.loads(hooks.read_text(encoding="utf-8"))
    commands = [item["hooks"][0]["command"] for item in removed["hooks"]["Stop"]]
    assert commands == ["user-stop"]
    assert not (tmp_path / "hooks" / "pactkit_stop.py").exists()


def test_capability_is_installed_but_not_validated_until_observed(tmp_path):
    from pactkit_codex.deployer import CodexDeployer

    CodexDeployer.deploy_stop_hook(tmp_path)

    capability = CodexDeployer.continuation_capabilities(tmp_path)

    assert capability["completion_hook"] is False
    assert capability["hook_installed"] is True
    assert capability["hook_trusted"] is False
    assert capability["auto_resume_available"] is False
    assert capability["hook_protocol_version"] == 1
    assert capability["hook_sha256"] == hashlib.sha256(
        (tmp_path / "hooks" / "pactkit_stop.py").read_bytes()
    ).hexdigest()


def test_deployed_hook_uses_only_codex_supported_fields(tmp_path):
    from pactkit_codex.deployer import CodexDeployer

    CodexDeployer.deploy_stop_hook(tmp_path)
    entry = json.loads((tmp_path / "hooks.json").read_text())["hooks"]["Stop"][0]

    assert set(entry) == {"hooks"}
    assert set(entry["hooks"][0]) == {"type", "command", "timeout", "statusMessage"}


def test_console_handler_emits_one_valid_json_object_for_invalid_input():
    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path(__file__).parents[2] / "src")
    result = subprocess.run(
        [sys.executable, "-m", "pactkit_codex.stop_hook"],
        input="not-json", text=True, capture_output=True, check=False, env=env,
    )

    assert result.returncode == 0
    assert json.loads(result.stdout)["decision"] == "block"
    assert result.stderr == ""


def test_full_deploy_manifest_reports_installed_not_validated(tmp_path):
    from pactkit_codex.deployer import CodexDeployer

    CodexDeployer().deploy(target=tmp_path)

    manifest = json.loads((tmp_path / ".pactkit-deployed.json").read_text())
    capability = manifest["workflow_continuation"]
    assert capability["hook_installed"] is True
    assert capability["completion_hook"] is False
    assert capability["continuation_validated"] is False
    assert capability["hook_sha256"]


def test_hook_records_sanitized_observation_and_validates_block_then_done(tmp_path, monkeypatch):
    from pactkit.continuation import ContinuationEngine
    from pactkit_codex.deployer import CodexDeployer
    from pactkit_codex.stop_hook import handle_stop

    codex_root = tmp_path / "codex-home"
    project = tmp_path / "project"
    project.mkdir()
    monkeypatch.setenv("CODEX_HOME", str(codex_root))
    CodexDeployer.deploy_stop_hook(codex_root)
    (codex_root / ".pactkit-deployed.json").write_text(json.dumps({
        "format": "codex",
        "workflow_continuation": CodexDeployer.continuation_capabilities(codex_root),
    }))
    engine = ContinuationEngine(project)
    state = engine.start("project-debug", evidence={"started": True})
    engine.bind_host_session(state["run_id"], session_id="secret-session")

    blocked = handle_stop(_event(project, session_id="secret-session"))
    assert blocked["decision"] == "block"
    for step in ("hypotheses_tested", "root_cause_found"):
        engine.checkpoint(state["run_id"], step_id=step, evidence={"phase": "verified"})
    engine.checkpoint(
        state["run_id"], step_id="completed", status="completed",
        evidence={"root_cause": "cause", "evidence": ["proof"], "next_action": "fix"},
    )
    assert handle_stop(_event(project, session_id="secret-session", turn_id="turn-2")) == {}

    observation = json.loads((codex_root / "pactkit-hook-state.json").read_text())
    serialized = json.dumps(observation)
    assert "secret-session" not in serialized
    assert "progress only" not in serialized
    assert observation["hook_sha256"] == hashlib.sha256(
        (codex_root / "hooks" / "pactkit_stop.py").read_bytes()
    ).hexdigest()
    assert observation["runs"][state["run_id"]]["block_observed"] is True
    assert observation["runs"][state["run_id"]]["done_observed"] is True
    traces = (codex_root / "pactkit-hook-observations.jsonl").read_text().splitlines()
    assert len(traces) == 2
    assert all("secret-session" not in line and "progress only" not in line for line in traces)
    capability = CodexDeployer.continuation_capabilities(codex_root)
    assert capability["hook_observed"] is True
    assert capability["hook_trusted"] is True
    assert capability["continuation_validated"] is True
    assert capability["completion_hook"] is True
    assert capability["auto_resume_available"] is True
    assert capability["guarantee_level"] == "host"
    deployed = json.loads((codex_root / ".pactkit-deployed.json").read_text())
    assert deployed["workflow_continuation"]["completion_hook"] is True
    assert deployed["workflow_continuation"]["continuation_validated"] is True

    (codex_root / "hooks" / "pactkit_stop.py").write_text("changed")
    assert CodexDeployer.continuation_capabilities(codex_root)["completion_hook"] is False


def test_bypass_observation_does_not_claim_persisted_trust(tmp_path, monkeypatch):
    from pactkit.continuation import ContinuationEngine
    from pactkit_codex.deployer import CodexDeployer
    from pactkit_codex.stop_hook import handle_stop

    codex_root = tmp_path / "codex-home"
    project = tmp_path / "project"
    project.mkdir()
    monkeypatch.setenv("CODEX_HOME", str(codex_root))
    monkeypatch.setenv("PACTKIT_CODEX_HOOK_VALIDATION_MODE", "bypass")
    engine = ContinuationEngine(project)
    engine.start("project-debug", evidence={"started": True})

    assert handle_stop(_event(project))["decision"] == "block"
    capability = CodexDeployer.continuation_capabilities(codex_root)
    assert capability["hook_observed"] is True
    assert capability["hook_trusted"] is False
    assert capability["completion_hook"] is False


def test_capability_does_not_combine_different_runs(tmp_path):
    from pactkit_codex.deployer import CodexDeployer, PACTKIT_HOOK_PROTOCOL_VERSION

    CodexDeployer.deploy_stop_hook(tmp_path)
    hook_hash = hashlib.sha256((tmp_path / "hooks" / "pactkit_stop.py").read_bytes()).hexdigest()
    (tmp_path / "pactkit-hook-state.json").write_text(json.dumps({
        "observed": True,
        "validation_mode": "host",
        "hook_protocol_version": PACTKIT_HOOK_PROTOCOL_VERSION,
        "hook_sha256": hook_hash,
        "runs": {
            "run-a": {"block_observed": True, "done_observed": False},
            "run-b": {"block_observed": False, "done_observed": True},
        },
    }))

    capability = CodexDeployer.continuation_capabilities(tmp_path)
    assert capability["hook_observed"] is True
    assert capability["continuation_validated"] is False
    assert capability["completion_hook"] is False
