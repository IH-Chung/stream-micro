"""Loopback-only FastAPI application for Deck Bridge."""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles

from .bridge import BridgeError, BridgeService
from .control_config import ControlConfigError
from .device import DeviceError, discover_mk2_devices
from .plugins.opencode import OpenCodeError


def create_app(config_path: Path | str, *, service: BridgeService | None = None) -> FastAPI:
    service = service or BridgeService(config_path)
    app = FastAPI(title="Deck Bridge", docs_url=None, redoc_url=None)
    app.state.bridge = service

    @app.get("/api/config")
    def get_config() -> dict[str, Any]:
        return service.config_data()

    @app.put("/api/config")
    def put_config(data: dict[str, Any]) -> dict[str, Any]:
        try:
            return service.replace_config(data)
        except ControlConfigError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    @app.get("/api/plugins")
    def get_plugins() -> list[dict[str, Any]]:
        return service.manifests()

    @app.get("/api/devices")
    def get_devices() -> list[dict[str, str | int | None]]:
        try:
            return discover_mk2_devices()
        except DeviceError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc

    @app.get("/api/status")
    def get_status(include_plugins: bool = True) -> dict[str, Any]:
        return service.status_data(include_plugins=include_plugins)

    @app.get("/api/opencode/servers")
    def get_opencode_servers() -> list[dict[str, str]]:
        try:
            return service.opencode_servers()
        except (BridgeError, OpenCodeError) as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc

    @app.get("/api/opencode/sessions")
    def get_opencode_sessions() -> list[dict[str, Any]]:
        try:
            return service.opencode_sessions()
        except (BridgeError, OpenCodeError) as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc

    @app.post("/api/opencode/sessions/{session_id}/select")
    def select_opencode_session(session_id: str) -> dict[str, str]:
        """Use OpenChamber Desktop to select the exact OpenCode Session."""

        try:
            return service.select_session_in_openchamber(session_id)
        except (BridgeError, OpenCodeError) as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    @app.post("/api/opencode/sessions/{session_id}/capture-window")
    def capture_session_window(session_id: str) -> dict[str, str]:
        try:
            return service.capture_session_window(session_id)
        except BridgeError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    @app.post("/api/opencode/sessions/{session_id}/confirm-window")
    def confirm_session_window(session_id: str) -> dict[str, Any]:
        try:
            return service.confirm_session_window(session_id)
        except BridgeError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    @app.post("/api/opencode/sessions/{session_id}/focus-window")
    def focus_session_window(session_id: str) -> dict[str, bool]:
        try:
            service.focus_session_window(session_id)
            return {"ok": True}
        except BridgeError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    @app.post("/api/actions")
    def post_action(data: dict[str, Any]) -> Any:
        plugin = data.get("plugin")
        action = data.get("action")
        params = data.get("params", {})
        if (
            not isinstance(plugin, str)
            or not isinstance(action, str)
            or not isinstance(params, dict)
        ):
            raise HTTPException(status_code=422, detail="plugin, action, and params are required")
        try:
            return service.invoke(plugin, action, params)
        except (BridgeError, OpenCodeError) as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    @app.post("/api/deck/keys/{key_index}/press")
    def post_deck_key_press(key_index: int) -> dict[str, Any]:
        try:
            return service.press_key(key_index)
        except (BridgeError, OpenCodeError) as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    @app.get("/api/events")
    async def get_events() -> StreamingResponse:
        async def stream() -> AsyncIterator[str]:
            while True:
                payload = json.dumps(service.status_data(), default=str)
                yield f"event: status\ndata: {payload}\n\n"
                await asyncio.sleep(service.config.bridge.refresh_interval_seconds)

        return StreamingResponse(stream(), media_type="text/event-stream")

    dashboard_dir = Path(__file__).resolve().parents[2] / "frontend" / "dist"
    if (dashboard_dir / "index.html").is_file():
        app.mount("/", StaticFiles(directory=dashboard_dir, html=True), name="dashboard")

    return app
