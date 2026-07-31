from pathlib import Path

from stream_micro.bridge import BridgeService
from stream_micro.control_config import (
    control_config_data,
    default_control_config,
    parse_control_config,
    write_control_config,
)
from stream_micro.deck_bridge import Mk2BridgeRunner
from stream_micro.plugins.base import AgentSession, SessionState


class RecordingService(BridgeService):
    def __init__(self, path: Path) -> None:
        super().__init__(path, plugins={})
        self.calls: list[tuple[str, str, dict[str, str]]] = []
        self.captured: list[str] = []
        self.focused: list[str] = []
        self.gui_selected: list[AgentSession] = []

    def invoke(self, plugin_id: str, action: str, params: dict[str, str]):
        self.calls.append((plugin_id, action, params))
        return {}

    def capture_session_window(self, session_id: str):
        self.captured.append(session_id)
        return {"executable": "x", "window_class": "y", "title_pattern": "z"}

    def focus_session_window(self, session_id: str) -> None:
        self.focused.append(session_id)

    def select_openchamber_session(self, session: AgentSession) -> None:
        self.gui_selected.append(session)


def test_session_key_ignores_legacy_window_binding(tmp_path: Path) -> None:
    path = tmp_path / "bridge.yaml"
    config = default_control_config()
    data = {
        **control_config_data(config),
        "session_window_bindings": {
            "session-1": {"executable": "x", "window_class": "y", "title_pattern": "z"}
        },
    }
    write_control_config(path, parse_control_config(data))
    service = RecordingService(path)
    runner = Mk2BridgeRunner(service)
    runner.sessions = (AgentSession("session-1", "Test", SessionState.IDLE),)
    service.active_sessions = runner.sessions

    runner.press(0)

    assert [session.id for session in service.gui_selected] == ["session-1"]
    assert service.focused == []


def test_session_key_selects_the_matching_openchamber_session(tmp_path: Path) -> None:
    path = tmp_path / "bridge.yaml"
    write_control_config(path, default_control_config())
    service = RecordingService(path)
    runner = Mk2BridgeRunner(service)
    runner.sessions = (AgentSession("session-1", "Test", SessionState.IDLE),)
    service.active_sessions = runner.sessions

    result = service.press_key(0)

    assert result == {"result": "session_selected_in_openchamber", "session_id": "session-1"}
    assert [session.id for session in service.gui_selected] == ["session-1"]
    assert service.calls == []
    assert service.captured == []


def test_span_child_key_selects_its_session_slot(tmp_path: Path) -> None:
    """A child key inside a span zone selects the Session at its slot offset."""

    path = tmp_path / "bridge.yaml"
    data = control_config_data(default_control_config())
    # Key 0 is span=5 session zone; press key 3 → slot 3 → session-4
    write_control_config(path, parse_control_config(data))
    service = RecordingService(path)
    service.active_sessions = tuple(
        AgentSession(f"session-{index}", f"Test {index}", SessionState.IDLE)
        for index in range(1, 6)
    )

    result = service.press_key(3)

    assert result == {"result": "session_selected_in_openchamber", "session_id": "session-4"}
    assert [session.id for session in service.gui_selected] == ["session-4"]
    assert service.calls == []


def test_standalone_session_key_on_key_6(tmp_path: Path) -> None:
    """A span=1 session key placed on key 6 selects the first available Session."""

    path = tmp_path / "bridge.yaml"
    data = control_config_data(default_control_config())
    data["buttons"][6].update(
        {"plugin": "opencode", "component": "session", "span": 1, "action": "select_session"}
    )
    write_control_config(path, parse_control_config(data))
    service = RecordingService(path)
    service.active_sessions = tuple(
        AgentSession(f"session-{index}", f"Test {index}", SessionState.IDLE)
        for index in range(1, 8)
    )

    result = service.press_key(6)

    assert result == {"result": "session_selected_in_openchamber", "session_id": "session-1"}
    assert [session.id for session in service.gui_selected] == ["session-1"]
