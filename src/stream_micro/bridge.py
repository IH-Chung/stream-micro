"""Local control-plane service shared by the API and Stream Deck loop."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .control_config import (
    ButtonBinding,
    ControlConfig,
    control_config_data,
    load_control_config,
    parse_control_config,
    write_control_config,
)
from .openchamber import (
    OpenChamberDesktop,
    OpenChamberError,
    discover_openchamber_desktop,
    select_openchamber_session,
)
from .plugins.base import AgentSession, BridgePlugin, PluginSnapshot
from .plugins.claude_code import ClaudeCodePlugin
from .plugins.codex import CodexPlugin
from .plugins.ollama_quota import OllamaQuotaPlugin
from .plugins.opencode import OpenCodePlugin
from .windows import (
    WindowCaptureError,
    focus_window_binding,
    foreground_window_binding,
)


class BridgeError(RuntimeError):
    pass


class BridgeService:
    """Owns loaded configuration, providers, and selected dashboard Session."""

    def __init__(
        self, config_path: Path | str, *, plugins: dict[str, BridgePlugin] | None = None
    ) -> None:
        self.config_path = Path(config_path)
        self.config = load_control_config(self.config_path)
        self.openchamber = None if plugins is not None else discover_openchamber_desktop()
        self.plugins = plugins or self._build_plugins(self.config, self.openchamber)
        self.selected_session_id: str | None = None
        self.selected_session_ids: dict[str, str] = {}
        self.pending_window_bindings: dict[str, dict[str, str]] = {}
        self.active_sessions_by_plugin: dict[str, tuple[AgentSession, ...]] = {}
        # Compatibility for callers that still populate the OpenCode list directly.
        self.active_sessions: tuple[AgentSession, ...] = ()
        self.device_status: dict[str, Any] = {
            "connected": False,
            "detail": "Waiting for Stream Deck",
        }

    @staticmethod
    def _build_plugins(
        config: ControlConfig, openchamber: OpenChamberDesktop | None = None
    ) -> dict[str, BridgePlugin]:
        plugins: dict[str, BridgePlugin] = {}
        open_code = config.plugins.get("opencode")
        if open_code and open_code.get("enabled", True):
            open_code_config = dict(open_code)
            if openchamber is not None:
                configured = open_code_config.get("endpoints", [])
                open_code_config["endpoints"] = list(
                    dict.fromkeys([openchamber.opencode_proxy_url, *configured])
                )
            plugins["opencode"] = OpenCodePlugin(open_code_config)
        ollama = config.plugins.get("ollama_quota")
        if ollama is not None:
            plugins["ollama_quota"] = OllamaQuotaPlugin(ollama)
        codex = config.plugins.get("codex")
        if codex and codex.get("enabled", False):
            plugins["codex"] = CodexPlugin(codex)
        claude_code = config.plugins.get("claude_code")
        if claude_code and claude_code.get("enabled", False):
            plugins["claude_code"] = ClaudeCodePlugin(claude_code)
        return plugins

    def config_data(self) -> dict[str, Any]:
        return control_config_data(self.config)

    def public_config_data(self) -> dict[str, Any]:
        """Return browser-safe configuration without persisted credentials."""

        data = self.config_data()
        ollama = data.get("plugins", {}).get("ollama_quota")
        if isinstance(ollama, dict):
            cookie = ollama.get("cookie_value")
            ollama["cookie_configured"] = isinstance(cookie, str) and bool(cookie)
            ollama["cookie_value"] = ""
        return data

    def replace_config(self, data: dict[str, Any]) -> dict[str, Any]:
        normalized = deepcopy(data)
        ollama = normalized.get("plugins", {}).get("ollama_quota")
        if isinstance(ollama, dict):
            configured = ollama.pop("cookie_configured", False)
            if ollama.get("cookie_value") == "" and configured is True:
                existing = self.config.plugins.get("ollama_quota", {}).get("cookie_value")
                if isinstance(existing, str) and existing:
                    ollama["cookie_value"] = existing
        config = parse_control_config(normalized)
        write_control_config(self.config_path, config)
        old_plugins = self.plugins
        self.config = config
        self.plugins = self._build_plugins(config, self.openchamber)
        self._close_plugins(old_plugins)
        enabled = set(self.plugins)
        self.selected_session_ids = {
            plugin_id: session_id
            for plugin_id, session_id in self.selected_session_ids.items()
            if plugin_id in enabled
        }
        if self.selected_session_id not in self.selected_session_ids.values():
            self.selected_session_id = None
        return self.public_config_data()

    def manifests(self) -> list[dict[str, Any]]:
        return [asdict(plugin.manifest) for plugin in self.plugins.values()]

    def snapshots(self) -> dict[str, PluginSnapshot]:
        return {plugin_id: plugin.snapshot() for plugin_id, plugin in self.plugins.items()}

    def snapshots_data(self) -> dict[str, dict[str, Any]]:
        """Return every provider snapshot without hard-coding a session source."""

        return {plugin_id: asdict(snapshot) for plugin_id, snapshot in self.snapshots().items()}

    def set_active_snapshots(self, snapshots: dict[str, PluginSnapshot]) -> None:
        """Cache the exact per-provider session lists currently rendered on the Deck."""

        self.active_sessions_by_plugin = {
            plugin_id: snapshot.sessions for plugin_id, snapshot in snapshots.items()
        }
        self.active_sessions = self.active_sessions_by_plugin.get("opencode", ())

    def status_data(self, *, include_plugins: bool = True) -> dict[str, Any]:
        """Return Bridge state, optionally without expensive Plugin snapshots."""

        status: dict[str, Any] = {
            "selected_session_id": self.selected_session_id,
            "selected_session_ids": dict(self.selected_session_ids),
            "pending_window_bindings": self.pending_window_bindings,
            "device": self.device_status,
            "openchamber": {
                "connected": self.openchamber is not None,
                "detail": (
                    f"OpenChamber Desktop {self.openchamber.version}"
                    if self.openchamber is not None
                    else "OpenChamber Desktop was not discovered on loopback"
                ),
                "url": self.openchamber.url if self.openchamber is not None else None,
            },
        }
        if include_plugins:
            status["plugins"] = {
                plugin_id: asdict(snapshot) for plugin_id, snapshot in self.snapshots().items()
            }
        return status

    def capture_session_window(self, session_id: str) -> dict[str, str]:
        if not isinstance(session_id, str) or not session_id:
            raise BridgeError("session_id is required")
        try:
            binding = foreground_window_binding()
        except WindowCaptureError as exc:
            raise BridgeError(str(exc)) from exc
        self.pending_window_bindings[session_id] = binding
        self.selected_session_id = session_id
        return binding

    def confirm_session_window(self, session_id: str) -> dict[str, Any]:
        try:
            binding = self.pending_window_bindings.pop(session_id)
        except KeyError as exc:
            raise BridgeError("No captured window binding is waiting for confirmation") from exc
        data = self.config_data()
        data["session_window_bindings"][session_id] = binding
        return self.replace_config(data)

    def focus_session_window(self, session_id: str) -> None:
        try:
            binding = self.config.session_window_bindings[session_id]
        except KeyError as exc:
            raise BridgeError("Session has no confirmed window binding") from exc
        try:
            focus_window_binding(binding)
        except WindowCaptureError as exc:
            raise BridgeError(str(exc)) from exc

    def select_openchamber_session(self, session: AgentSession) -> None:
        try:
            select_openchamber_session(
                session_id=session.id,
                directory=session.directory,
            )
        except OpenChamberError as exc:
            raise BridgeError(str(exc)) from exc

    def select_session_in_openchamber(self, session_id: str) -> dict[str, str]:
        """Focus one current OpenCode Session in OpenChamber Desktop by ID."""

        if not isinstance(session_id, str) or not session_id.strip():
            raise BridgeError("session_id is required")
        plugin = self._plugin("opencode")
        if not isinstance(plugin, OpenCodePlugin):
            raise BridgeError("OpenCode plugin is not enabled")
        session = next(
            (item for item in plugin.sessions() if item.id == session_id),
            None,
        )
        if session is None:
            raise BridgeError("Session no longer exists on the active OpenCode server")
        self._select_openchamber_session(session)
        return {"result": "session_selected_in_openchamber", "session_id": session.id}

    def _select_openchamber_session(self, session: AgentSession) -> None:
        self.select_openchamber_session(session)
        self.selected_session_id = session.id
        self.selected_session_ids["opencode"] = session.id
        plugin = self.plugins.get("opencode")
        if isinstance(plugin, OpenCodePlugin):
            plugin.mark_viewed(session.id)

    def press_key(self, key_index: int) -> dict[str, Any]:
        """Dispatch one MK.2 key press; shared by HID and local diagnostics."""

        if not isinstance(key_index, int) or not 0 <= key_index < len(self.config.buttons):
            raise BridgeError("key_index must be an MK.2 key from 0 through 14")
        binding = self.config.buttons[key_index]
        parent = self._span_parent(key_index)
        # If this key is inside a span parent, dispatch through the parent.
        if parent is not None and parent != binding:
            return self._press_span_child(parent, key_index)
        if parent is not None:
            return self._press_span_child(parent, key_index)
        if binding.plugin and binding.action:
            params = dict(binding.action_params)
            if binding.session_id:
                params.setdefault("session_id", binding.session_id)
            return self.invoke(binding.plugin, binding.action, params)
        return {"result": "no_action"}

    def _span_parent(self, key_index: int) -> ButtonBinding | None:
        """Return the span zone root that owns ``key_index``, or None.

        A span-1 session key is its own zone root so it dispatches via the
        slot-based session selector, not the generic action dispatcher.
        """
        for b in self.config.buttons:
            if (
                b.plugin
                and b.component == "session"
                and b.key_index <= key_index < b.key_index + max(b.span, 1)
            ):
                return b
        return None

    def _press_span_child(
        self, parent: ButtonBinding, key_index: int
    ) -> dict[str, Any]:
        if not parent.plugin or not parent.action:
            return {"result": "no_action"}
        sessions = self._sessions_for_plugin(parent.plugin)
        slot = key_index - parent.key_index
        # span > 1: sessions auto-assigned by slot, ignore session_id.
        # span = 1: session_id pins to one session; fallback to slot 0.
        if parent.span > 1:
            if slot < len(sessions):
                session = sessions[slot]
                params = {**parent.action_params, "session_id": session.id}
                return self.invoke(parent.plugin, parent.action, params)
            return {"result": "no_action"}
        if parent.session_id:
            session = next(
                (s for s in sessions if s.id == parent.session_id),
                None,
            )
            if session is None:
                raise BridgeError(f"Session {parent.session_id} is no longer active")
            params = {**parent.action_params, "session_id": session.id}
            return self.invoke(parent.plugin, parent.action, params)
        if sessions:
            params = {**parent.action_params, "session_id": sessions[0].id}
            return self.invoke(parent.plugin, parent.action, params)
        return {"result": "no_action"}

    def _sessions_for_plugin(self, plugin_id: str) -> tuple[AgentSession, ...]:
        sessions = self.active_sessions_by_plugin.get(plugin_id)
        if sessions is not None:
            return sessions
        if plugin_id == "opencode":
            return self.active_sessions
        return ()

    def opencode_servers(self) -> list[dict[str, str]]:
        plugin = self._plugin("opencode")
        if not isinstance(plugin, OpenCodePlugin):
            raise BridgeError("OpenCode plugin is not enabled")
        return [asdict(endpoint) for endpoint in plugin.discover()]

    def opencode_sessions(self) -> list[dict[str, Any]]:
        plugin = self._plugin("opencode")
        if not isinstance(plugin, OpenCodePlugin):
            raise BridgeError("OpenCode plugin is not enabled")
        return [asdict(session) for session in plugin.sessions()]

    def handle_claude_code_hook(self, payload: dict[str, Any]) -> dict[str, str | bool | None]:
        plugin = self._plugin("claude_code")
        if not isinstance(plugin, ClaudeCodePlugin):
            raise BridgeError("Claude Code plugin is not enabled")
        return plugin.handle_hook(payload)

    def handle_claude_code_quota(self, payload: dict[str, Any]) -> dict[str, str | bool | None]:
        plugin = self._plugin("claude_code")
        if not isinstance(plugin, ClaudeCodePlugin):
            raise BridgeError("Claude Code plugin is not enabled")
        return plugin.handle_quota(payload)

    def invoke(self, plugin_id: str, action: str, params: dict[str, Any]) -> Any:
        plugin = self._plugin(plugin_id)
        if action not in plugin.manifest.actions:
            raise BridgeError(f"Action {action} is not allowed for plugin {plugin_id}")
        # ``select_session`` is a Bridge action: OpenCode supplies the list,
        # while OpenChamber Desktop owns the visible Session selection.
        # Keeping this interception makes legacy API callers follow the same
        # path as a physical Session key and the Dashboard.
        if plugin_id == "opencode" and action == "select_session":
            session_id = params.get("session_id")
            if not isinstance(session_id, str) or not session_id:
                raise BridgeError("select_session requires session_id")
            return self.select_session_in_openchamber(session_id)
        result = plugin.invoke(action, params)
        if action == "select_session":
            session_id = params.get("session_id")
            if isinstance(session_id, str) and session_id:
                self.selected_session_id = session_id
                self.selected_session_ids[plugin_id] = session_id
        return result

    def _plugin(self, plugin_id: str) -> BridgePlugin:
        try:
            return self.plugins[plugin_id]
        except KeyError as exc:
            raise BridgeError(f"Plugin {plugin_id} is not enabled") from exc

    @staticmethod
    def _close_plugins(plugins: dict[str, BridgePlugin]) -> None:
        for plugin in plugins.values():
            close = getattr(plugin, "close", None)
            if callable(close):
                close()

    def close(self) -> None:
        self._close_plugins(self.plugins)
