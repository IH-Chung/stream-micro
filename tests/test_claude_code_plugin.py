from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from stream_micro.bridge import BridgeService
from stream_micro.control_config import (
    control_config_data,
    default_control_config,
    parse_control_config,
    write_control_config,
)
from stream_micro.plugins.base import SessionState
from stream_micro.plugins.claude_code import (
    ClaudeCodeError,
    ClaudeCodePlugin,
    launch_claude_session,
    map_claude_hook_state,
    parse_claude_rate_limits,
    read_claude_history,
    validate_claude_code_config,
)


def _write_history(path: Path, *records: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(f"{json.dumps(record)}\n" for record in records), encoding="utf-8")


def test_history_returns_recent_unique_sessions_with_display_titles(tmp_path: Path) -> None:
    history = tmp_path / "history.jsonl"
    _write_history(
        history,
        {
            "sessionId": "older",
            "display": "First task",
            "project": str(tmp_path / "one"),
            "timestamp": 100,
        },
        {"not": "a session"},
        {
            "sessionId": "newer",
            "display": "  Add   the Claude provider  ",
            "project": str(tmp_path / "two"),
            "timestamp": 300,
        },
        {
            "sessionId": "older",
            "display": "Updated task",
            "project": str(tmp_path / "one"),
            "timestamp": 200,
        },
    )

    sessions = read_claude_history(history)

    assert [session.id for session in sessions] == ["newer", "older"]
    assert sessions[0].title == "Add the Claude provider"
    assert sessions[1].title == "Updated task"


@pytest.mark.parametrize(
    ("payload", "expected"),
    [
        ({"hook_event_name": "SessionStart", "source": "startup"}, SessionState.IDLE),
        ({"hook_event_name": "SessionStart", "source": "compact"}, SessionState.RUNNING),
        ({"hook_event_name": "UserPromptSubmit"}, SessionState.RUNNING),
        ({"hook_event_name": "PermissionRequest"}, SessionState.WAITING),
        (
            {"hook_event_name": "Notification", "notification_type": "permission_prompt"},
            SessionState.WAITING,
        ),
        (
            {"hook_event_name": "Notification", "notification_type": "idle_prompt"},
            SessionState.COMPLETED,
        ),
        ({"hook_event_name": "Stop"}, SessionState.COMPLETED),
        ({"hook_event_name": "StopFailure"}, SessionState.ERROR),
        ({"hook_event_name": "SessionEnd"}, SessionState.IDLE),
        ({"hook_event_name": "Unknown"}, None),
    ],
)
def test_hook_events_map_to_deck_states(
    payload: dict[str, object], expected: SessionState | None
) -> None:
    assert map_claude_hook_state(payload) is expected


def test_plugin_merges_history_with_live_hooks_and_resumes_exact_session(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    project.mkdir()
    _write_history(
        tmp_path / "history.jsonl",
        {
            "sessionId": "session-1",
            "display": "Initial task",
            "project": str(project),
            "timestamp": 100,
        },
    )
    launched: list[tuple[str, str | None]] = []
    plugin = ClaudeCodePlugin(
        {
            "enabled": True,
            "claude_path": None,
            "claude_home": str(tmp_path),
            "max_sessions": 15,
        },
        launcher=lambda session_id, directory: launched.append((session_id, directory)),
        clock=lambda: 1.0,
    )

    accepted = plugin.handle_hook(
        {
            "session_id": "session-1",
            "cwd": str(project),
            "hook_event_name": "UserPromptSubmit",
            "prompt": "Implement the Stream Deck integration",
        }
    )
    snapshot = plugin.snapshot()
    result = plugin.invoke("select_session", {"session_id": "session-1"})

    assert accepted == {"accepted": True, "session_id": "session-1", "state": "running"}
    assert snapshot.health.connected is True
    assert snapshot.sessions[0].title == "Implement the Stream Deck integration"
    assert snapshot.sessions[0].state is SessionState.RUNNING
    assert snapshot.sessions[0].project == "project"
    assert result == {
        "result": "session_selected_in_claude_code",
        "session_id": "session-1",
    }
    assert launched == [("session-1", str(project))]


def test_plugin_rejects_malformed_hooks_and_unknown_sessions(tmp_path: Path) -> None:
    plugin = ClaudeCodePlugin(
        {"enabled": True, "claude_home": str(tmp_path)}, launcher=lambda _id, _cwd: None
    )

    with pytest.raises(ClaudeCodeError, match="requires session_id"):
        plugin.handle_hook({"hook_event_name": "Stop"})
    with pytest.raises(ClaudeCodeError, match="no longer exists"):
        plugin.invoke("select_session", {"session_id": "missing"})


def test_status_line_rate_limits_become_generic_quota_signals(tmp_path: Path) -> None:
    payload = {
        "session_id": "session-1",
        "rate_limits": {
            "five_hour": {"used_percentage": 23.5, "resets_at": 1_738_425_600},
            "seven_day": {"used_percentage": 41.2, "resets_at": 1_738_857_600},
        },
    }
    plugin = ClaudeCodePlugin(
        {"enabled": True, "claude_home": str(tmp_path)}, launcher=lambda _id, _cwd: None
    )

    result = plugin.handle_quota(payload)
    snapshot = plugin.snapshot()

    assert parse_claude_rate_limits(payload) == {
        "primary_percent": 23.5,
        "primary_label": "5H",
        "primary_reset_at": "2025-02-01T16:00:00+00:00",
        "secondary_percent": 41.2,
        "secondary_label": "7D",
        "secondary_reset_at": "2025-02-06T16:00:00+00:00",
    }
    assert result["quota_updated"] is True
    assert snapshot.signals == parse_claude_rate_limits(payload)
    assert plugin.manifest.components == ("session", "quota")


def test_missing_status_line_limits_keep_the_last_known_quota(tmp_path: Path) -> None:
    plugin = ClaudeCodePlugin(
        {"enabled": True, "claude_home": str(tmp_path)}, launcher=lambda _id, _cwd: None
    )
    plugin.handle_quota(
        {"rate_limits": {"five_hour": {"used_percentage": 10, "resets_at": 1000}}}
    )

    result = plugin.handle_quota({"session_id": "new-session"})
    signals = plugin.snapshot().signals

    assert result["quota_updated"] is False
    assert signals is not None
    assert signals["primary_percent"] == 10.0


def test_windows_resume_launches_the_exact_session_with_the_companion_plugin(
    tmp_path: Path,
) -> None:
    companion = tmp_path / "companion"
    companion.mkdir()
    with (
        patch("stream_micro.plugins.claude_code.os.name", "nt"),
        patch(
            "stream_micro.plugins.claude_code.resolve_claude_command",
            return_value=["claude.exe"],
        ),
        patch("stream_micro.plugins.claude_code.subprocess.Popen") as popen,
    ):
        launch_claude_session(
            "session-1",
            str(tmp_path),
            claude_path="claude",
            plugin_dir=str(companion),
        )

    assert popen.call_args.args[0] == [
        "claude.exe",
        "--plugin-dir",
        str(companion),
        "--resume",
        "session-1",
    ]
    assert popen.call_args.kwargs["cwd"] == str(tmp_path)
    assert popen.call_args.kwargs["shell"] is False


@pytest.mark.parametrize(
    ("config", "message"),
    [
        ({"enabled": "yes"}, "boolean"),
        ({"claude_path": ""}, "claude_path"),
        ({"plugin_dir": []}, "plugin_dir"),
        ({"max_sessions": 0}, "max_sessions"),
        ({"unknown": True}, "Unknown"),
    ],
)
def test_config_validation_rejects_invalid_values(
    config: dict[str, object], message: str
) -> None:
    with pytest.raises(ClaudeCodeError, match=message):
        validate_claude_code_config(config)


def test_bridge_registers_claude_code_only_when_enabled(tmp_path: Path) -> None:
    data = control_config_data(default_control_config())
    data["plugins"]["opencode"]["enabled"] = False
    data["plugins"]["ollama_quota"]["enabled"] = False
    data["plugins"]["claude_code"]["enabled"] = True
    data["plugins"]["claude_code"]["claude_home"] = str(tmp_path)
    path = tmp_path / "bridge.yaml"
    write_control_config(path, parse_control_config(data))

    service = BridgeService(path)
    try:
        assert isinstance(service.plugins["claude_code"], ClaudeCodePlugin)
    finally:
        service.close()
