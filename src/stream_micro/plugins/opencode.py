"""OpenCode local-server adapter.

The adapter deliberately uses only documented, safe server endpoints. Window
focus and Stream Deck rendering stay in the Bridge layer.
"""

from __future__ import annotations

import re
import subprocess
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import PureWindowsPath
from typing import Any

import httpx

from .base import AgentSession, PluginHealth, PluginManifest, PluginSnapshot, SessionState


class OpenCodeError(RuntimeError):
    pass


LIVE_STATE_SESSION_LIMIT = 5


@dataclass(frozen=True)
class OpenCodeEndpoint:
    url: str


def listening_loopback_ports(netstat_output: str) -> set[int]:
    """Extract Windows TCP loopback listening ports without network scanning."""

    ports: set[int] = set()
    for line in netstat_output.splitlines():
        columns = line.split()
        if len(columns) < 4 or columns[0].upper() != "TCP" or columns[3].upper() != "LISTENING":
            continue
        address = columns[1]
        match = re.match(r"(?:127\.0\.0\.1|\[::1\]):(\d+)$", address)
        if match:
            ports.add(int(match.group(1)))
    return ports


def default_loopback_ports() -> set[int]:
    try:
        result = subprocess.run(
            ["netstat", "-ano", "-p", "tcp"],
            check=False,
            capture_output=True,
            text=True,
            timeout=3,
        )
    except (OSError, subprocess.SubprocessError):
        return set()
    return listening_loopback_ports(result.stdout)


class OpenCodePlugin:
    manifest = PluginManifest(
        id="opencode",
        name="OpenCode",
        components=("session",),
        actions=("select_session",),
    )

    def __init__(
        self,
        config: dict[str, Any],
        *,
        client: httpx.Client | None = None,
        port_provider: Callable[[], Iterable[int]] = default_loopback_ports,
    ) -> None:
        self.validate_config(config)
        self.config = config
        self._client = client or httpx.Client(timeout=3.0)
        self._port_provider = port_provider
        self.endpoint: OpenCodeEndpoint | None = None
        self._recently_busy: set[str] = set()
        self._completed: set[str] = set()

    def validate_config(self, config: dict[str, Any]) -> None:
        if not isinstance(config.get("enabled", True), bool):
            raise OpenCodeError("opencode.enabled must be true or false")
        endpoints = config.get("endpoints", [])
        if not isinstance(endpoints, list) or not all(isinstance(item, str) for item in endpoints):
            raise OpenCodeError("opencode.endpoints must be a list of URLs")
        password_env = config.get("password_env")
        if password_env is not None and (not isinstance(password_env, str) or not password_env):
            raise OpenCodeError(
                "opencode.password_env must be a non-empty environment variable name or null"
            )

    def _candidate_urls(self) -> list[str]:
        configured = [url.rstrip("/") for url in self.config.get("endpoints", [])]
        discovered = [f"http://127.0.0.1:{port}" for port in self._port_provider()]
        return list(dict.fromkeys([*configured, *discovered]))

    def discover(self) -> tuple[OpenCodeEndpoint, ...]:
        found: list[OpenCodeEndpoint] = []
        for url in self._candidate_urls():
            try:
                response = self._client.get(f"{url}/global/health")
                body = response.json()
            except (httpx.HTTPError, ValueError):
                continue
            if response.is_success and body.get("healthy") is True:
                found.append(OpenCodeEndpoint(url))
        self.endpoint = found[0] if found else None
        return tuple(found)

    def _require_endpoint(self) -> OpenCodeEndpoint:
        if self.endpoint is None:
            self.discover()
        if self.endpoint is None:
            raise OpenCodeError("No active OpenCode server found on this computer")
        return self.endpoint

    @staticmethod
    def _state(value: Any) -> SessionState:
        """Map an OpenCode ``SessionStatus.type`` string to a ``SessionState``.

        OpenCode v1.18.x reports three status types on ``/session/status``:
        ``idle``, ``busy``, and ``retry``.  ``busy`` means the agent is actively
        generating; ``retry`` means the upstream provider is retrying after an
        error (treated as ERROR); ``idle`` means no turn is in flight.
        """

        normalized = str(value or "idle").lower()
        if normalized == "busy":
            return SessionState.RUNNING
        if normalized == "retry":
            return SessionState.ERROR
        return SessionState.IDLE

    def _pending_session_ids(self, endpoint: OpenCodeEndpoint) -> set[str]:
        """Return session ids that have an unanswered permission or question.

        ``/permission`` and ``/question`` list pending approval/interaction
        requests.  A session with at least one pending request is WAITING for
        user input — the Deck key should show amber.

        On OpenCode v1.18.7+ the v1 endpoints may return empty for v2
        questions/permissions, so we also check the per-session v2 endpoints
        ``/api/session/{id}/question`` and ``/api/session/{id}/permission``.
        """

        pending: set[str] = set()
        for path in ("/permission", "/question"):
            try:
                response = self._client.get(f"{endpoint.url}{path}")
                response.raise_for_status()
                items = response.json()
            except (httpx.HTTPError, ValueError):
                continue
            if not isinstance(items, list):
                continue
            for item in items:
                if isinstance(item, dict) and isinstance(item.get("sessionID"), str):
                    pending.add(item["sessionID"])
        return pending

    def _pending_session_ids_v2(
        self, endpoint: OpenCodeEndpoint, session_ids: list[str]
    ) -> set[str]:
        """Check v2 per-session question/permission endpoints for pending items."""

        pending: set[str] = set()
        for sid in session_ids:
            for path in (f"/api/session/{sid}/question", f"/api/session/{sid}/permission"):
                try:
                    response = self._client.get(f"{endpoint.url}{path}")
                    response.raise_for_status()
                    body = response.json()
                except (httpx.HTTPError, ValueError):
                    continue
                items = body.get("data") if isinstance(body, dict) else body
                if isinstance(items, list) and items:
                    pending.add(sid)
                    break
        return pending

    def _active_session_ids(
        self, endpoint: OpenCodeEndpoint, session_ids: list[str]
    ) -> tuple[set[str], set[str]]:
        """Return ``(active, waiting)`` session-id sets from message polling.

        On OpenCode v1.18.7+ ``/session/status`` returns an empty map during
        tool execution (it only reports ``busy`` during LLM token generation).
        The reliable running indicator is the message list:

        - An assistant message whose ``time.completed`` is absent means the
          agent is actively generating or executing tools.
        - A tool part with ``state.status`` of ``running`` or ``pending`` means
          a tool call is in flight.

        A tool call whose ``tool`` name is ``question`` or ``permission`` is
        waiting for user input, not actively working — those session ids go into
        the ``waiting`` set so the Deck key shows amber instead of blue.

        One ``GET /session/:id/message?limit=1`` call per session is cheap
        (5 sessions × 5 s interval = 1 req/s) and authoritative.
        """

        active: set[str] = set()
        waiting: set[str] = set()
        for sid in session_ids:
            try:
                response = self._client.get(
                    f"{endpoint.url}/session/{sid}/message", params={"limit": 1}
                )
                response.raise_for_status()
                messages = response.json()
            except (httpx.HTTPError, ValueError):
                continue
            if not isinstance(messages, list) or not messages:
                continue
            msg = messages[-1] if isinstance(messages[-1], dict) else None
            if not msg:
                continue
            info = msg.get("info")
            if not isinstance(info, dict) or info.get("role") != "assistant":
                continue
            # Check tool parts FIRST — a question/permission tool in
            # running/pending state means the session is WAITING for user
            # input, even though time.completed is absent (the turn is
            # still open while the user hasn't answered).
            parts = msg.get("parts")
            classified = False
            if isinstance(parts, list):
                for part in parts:
                    if not isinstance(part, dict) or part.get("type") != "tool":
                        continue
                    state = part.get("state")
                    status = state.get("status") if isinstance(state, dict) else None
                    if status in ("running", "pending"):
                        tool_name = str(part.get("tool", ""))
                        if tool_name in ("question", "permission"):
                            waiting.add(sid)
                        else:
                            active.add(sid)
                        classified = True
                        break
            if classified:
                continue
            # Fall back to time/finish heuristics for sessions without
            # an explicit running/pending tool part.
            time_field = info.get("time")
            completed = time_field.get("completed") if isinstance(time_field, dict) else None
            if completed is None:
                active.add(sid)
                continue
            if not info.get("finish"):
                active.add(sid)
                continue
        return active, waiting

    def sessions(self) -> tuple[AgentSession, ...]:
        endpoint = self._require_endpoint()
        try:
            # `/session` is scoped by the server's current workspace on newer
            # OpenCode versions.  The experimental list is the cross-project
            # feed and carries the global last-update ordering we need.
            sessions_response = self._client.get(f"{endpoint.url}/experimental/session")
            if sessions_response.status_code == 404:
                sessions_response = self._client.get(f"{endpoint.url}/session")
            statuses_response = self._client.get(f"{endpoint.url}/session/status")
            sessions_response.raise_for_status()
            statuses_response.raise_for_status()
            raw_sessions = sessions_response.json()
            statuses = statuses_response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise OpenCodeError(f"Could not read OpenCode sessions: {exc}") from exc
        if not isinstance(raw_sessions, list) or not isinstance(statuses, dict):
            raise OpenCodeError("OpenCode returned an unexpected session response")
        pending = self._pending_session_ids(endpoint)
        live_ids: set[str] = set()
        result: list[AgentSession] = []
        candidate_ids: list[str] = []
        for item in sorted(raw_sessions, key=_updated_at, reverse=True):
            if not isinstance(item, dict) or not isinstance(item.get("id"), str):
                continue
            if isinstance(item.get("parentID"), str) and item["parentID"]:
                continue
            candidate_ids.append(item["id"])
        visible_candidate_ids = candidate_ids[:LIVE_STATE_SESSION_LIMIT]
        if visible_candidate_ids:
            pending |= self._pending_session_ids_v2(endpoint, visible_candidate_ids)
        # Always poll the last message of each session.  On OpenCode v1.18.7+
        # /session/status returns {} during tool execution — it only reports
        # "busy" during LLM token generation.  Message-based detection is the
        # authoritative signal for "agent is working".
        active_ids, waiting_ids = (
            self._active_session_ids(endpoint, visible_candidate_ids)
            if visible_candidate_ids
            else (set(), set())
        )
        pending |= waiting_ids
        for item in sorted(raw_sessions, key=_updated_at, reverse=True):
            if not isinstance(item, dict) or not isinstance(item.get("id"), str):
                continue
            if isinstance(item.get("parentID"), str) and item["parentID"]:
                continue
            session_id = item["id"]
            live_ids.add(session_id)
            status_value = statuses.get(session_id)
            if isinstance(status_value, dict):
                status_value = status_value.get("type") or status_value.get("status")
            directory = item.get("directory")
            project = _project_folder(directory, item.get("projectID"))
            if session_id in pending:
                state = SessionState.WAITING
                self._completed.discard(session_id)
            else:
                raw_state = self._state(status_value)
                if raw_state is SessionState.IDLE and session_id in active_ids:
                    raw_state = SessionState.RUNNING
                if raw_state is SessionState.RUNNING:
                    self._recently_busy.add(session_id)
                    self._completed.discard(session_id)
                    state = raw_state
                elif raw_state is SessionState.ERROR:
                    self._recently_busy.discard(session_id)
                    self._completed.discard(session_id)
                    state = raw_state
                elif session_id in self._recently_busy:
                    self._recently_busy.discard(session_id)
                    self._completed.add(session_id)
                    state = SessionState.COMPLETED
                else:
                    state = raw_state
            result.append(
                AgentSession(
                    id=session_id,
                    title=str(item.get("title") or "Untitled session"),
                    state=state,
                    project=project,
                    directory=directory if isinstance(directory, str) else None,
                )
            )
        self._recently_busy &= live_ids
        self._completed &= live_ids
        return tuple(result)

    def snapshot(self) -> PluginSnapshot:
        try:
            endpoint = self._require_endpoint()
            return PluginSnapshot(PluginHealth(True, "Connected", endpoint.url), self.sessions())
        except OpenCodeError as exc:
            return PluginSnapshot(PluginHealth(False, str(exc)), ())

    def mark_viewed(self, session_id: str) -> None:
        """Clear the COMPLETED flag after the user acknowledges the session."""
        self._completed.discard(session_id)

    def invoke(self, action: str, params: dict[str, Any]) -> Any:
        endpoint = self._require_endpoint()
        if action == "select_session":
            session_id = _required_string(params, "session_id")
            self.mark_viewed(session_id)
            response = self._client.post(
                f"{endpoint.url}/tui/select-session", json={"sessionID": session_id}
            )
        else:
            raise OpenCodeError(f"Unsupported OpenCode action: {action}")
        try:
            response.raise_for_status()
            return response.json() if response.content else {"ok": True}
        except (httpx.HTTPError, ValueError) as exc:
            raise OpenCodeError(f"OpenCode action failed: {exc}") from exc


def _required_string(params: dict[str, Any], name: str) -> str:
    value = params.get(name)
    if not isinstance(value, str) or not value.strip():
        raise OpenCodeError(f"{name} is required")
    return value


def _project_folder(directory: Any, project_id: Any) -> str | None:
    """Return the human-readable project folder that belongs on a Deck key."""

    if isinstance(directory, str) and directory.strip():
        name = PureWindowsPath(directory.rstrip("\\/")).name
        if name:
            return name
    return str(project_id) if isinstance(project_id, str) and project_id else None


def _updated_at(session: Any) -> int:
    if not isinstance(session, dict):
        return 0
    time = session.get("time")
    value = time.get("updated") if isinstance(time, dict) else None
    return value if isinstance(value, int) else 0
