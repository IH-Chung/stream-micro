from pathlib import Path
from typing import Any, cast

import httpx
from fastapi.testclient import TestClient

from stream_micro.control_config import default_control_config, write_control_config
from stream_micro.plugins.opencode import OpenCodePlugin
from stream_micro.server import create_app


def opencode_handler(request: httpx.Request) -> httpx.Response:
    if request.url.path == "/global/health":
        return httpx.Response(200, json={"healthy": True})
    if request.method == "GET" and request.url.path == "/session":
        return httpx.Response(200, json=[{"id": "session-1", "title": "Agent task"}])
    if request.url.path == "/session/status":
        return httpx.Response(200, json={"session-1": {"type": "idle"}})
    if request.method == "POST" and request.url.path == "/session":
        return httpx.Response(200, json={"id": "new-session"})
    return httpx.Response(404)


def app_with_plugin(tmp_path: Path) -> TestClient:
    config_path = tmp_path / "control.yaml"
    write_control_config(config_path, default_control_config())
    app = create_app(config_path)
    app.state.bridge.plugins["opencode"] = OpenCodePlugin(
        {"enabled": True, "endpoints": ["http://127.0.0.1:4096"], "password_env": None},
        client=httpx.Client(transport=httpx.MockTransport(opencode_handler)),
        port_provider=lambda: {4096},
    )
    return TestClient(app)


def test_local_api_returns_config_plugin_status_and_sessions(tmp_path: Path) -> None:
    with app_with_plugin(tmp_path) as client:
        config = client.get("/api/config")
        plugins = client.get("/api/plugins")
        status = client.get("/api/status")
        sessions = client.get("/api/opencode/sessions")

    assert config.status_code == 200
    assert config.json()["stream_deck"]["model"] == "mk2"
    assert plugins.json()[0]["id"] == "opencode"
    assert status.json()["plugins"]["opencode"]["health"]["connected"] is True
    assert sessions.json()[0]["id"] == "session-1"


def test_basic_status_skips_expensive_plugin_snapshots(tmp_path: Path, monkeypatch) -> None:
    """The dashboard heartbeat must not re-poll every OpenCode Session."""

    with app_with_plugin(tmp_path) as client:
        service = cast(Any, client.app).state.bridge
        monkeypatch.setattr(
            service,
            "snapshots",
            lambda: (_ for _ in ()).throw(AssertionError("snapshots should not run")),
        )
        response = client.get("/api/status?include_plugins=false")

    assert response.status_code == 200
    assert "plugins" not in response.json()


def test_action_rejects_actions_not_declared_by_plugin(tmp_path: Path) -> None:
    with app_with_plugin(tmp_path) as client:
        response = client.post(
            "/api/actions", json={"plugin": "opencode", "action": "shell", "params": {}}
        )

    assert response.status_code == 422
    assert "not allowed" in response.json()["detail"]


def test_session_select_endpoint_uses_openchamber_navigation(
    tmp_path: Path, monkeypatch
) -> None:
    selected: list[str] = []
    monkeypatch.setattr(
        "stream_micro.bridge.select_openchamber_session",
        lambda *, session_id, directory: selected.append(session_id),
    )
    with app_with_plugin(tmp_path) as client:
        response = client.post("/api/opencode/sessions/session-1/select")

    assert response.status_code == 200
    assert response.json() == {
        "result": "session_selected_in_openchamber",
        "session_id": "session-1",
    }
    assert selected == ["session-1"]


def test_legacy_select_action_uses_the_same_openchamber_navigation(
    tmp_path: Path, monkeypatch
) -> None:
    selected: list[str] = []
    monkeypatch.setattr(
        "stream_micro.bridge.select_openchamber_session",
        lambda *, session_id, directory: selected.append(session_id),
    )
    with app_with_plugin(tmp_path) as client:
        response = client.post(
            "/api/actions",
            json={
                "plugin": "opencode",
                "action": "select_session",
                "params": {"session_id": "session-1"},
            },
        )

    assert response.status_code == 200
    assert response.json()["result"] == "session_selected_in_openchamber"
    assert selected == ["session-1"]


def test_local_server_serves_built_dashboard(tmp_path: Path) -> None:
    with app_with_plugin(tmp_path) as client:
        response = client.get("/")

    assert response.status_code == 200
    assert 'id="root"' in response.text
