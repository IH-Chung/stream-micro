from pathlib import Path

from stream_micro.bridge import BridgeService
from stream_micro.control_config import (
    control_config_data,
    default_control_config,
    parse_control_config,
    write_control_config,
)


def test_captured_window_requires_confirmation_before_it_is_saved(
    tmp_path: Path, monkeypatch
) -> None:
    path = tmp_path / "bridge.yaml"
    write_control_config(path, default_control_config())
    service = BridgeService(path, plugins={})
    captured = {
        "executable": "C:\\OpenCode\\opencode.exe",
        "window_class": "ConsoleWindowClass",
        "title_pattern": "OpenCode",
    }
    monkeypatch.setattr("stream_micro.bridge.foreground_window_binding", lambda: captured)

    assert service.capture_session_window("session-1") == captured
    assert service.config.session_window_bindings == {}
    service.confirm_session_window("session-1")

    assert service.config.session_window_bindings["session-1"] == captured


def test_confirmed_binding_focuses_its_window(tmp_path: Path, monkeypatch) -> None:
    path = tmp_path / "bridge.yaml"
    config = default_control_config()
    data = {
        **control_config_data(config),
        "session_window_bindings": {
            "session-1": {
                "executable": "C:\\OpenCode\\opencode.exe",
                "window_class": "ConsoleWindowClass",
                "title_pattern": "OpenCode",
            }
        },
    }
    write_control_config(path, parse_control_config(data))
    service = BridgeService(path, plugins={})
    focused: list[dict[str, str]] = []
    monkeypatch.setattr("stream_micro.bridge.focus_window_binding", focused.append)

    service.focus_session_window("session-1")
    assert focused == [service.config.session_window_bindings["session-1"]]
