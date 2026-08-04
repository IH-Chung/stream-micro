"""Physical MK.2 refresh and press-dispatch loop."""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from threading import Event

from .bridge import BridgeError, BridgeService
from .control_config import ButtonBinding
from .control_renderer import render_control_key, render_quota_key
from .device import DeviceError, Mk2DeckOutput
from .plugins.base import AgentSession
from .plugins.opencode import OpenCodeError


class Mk2BridgeRunner:
    def __init__(self, service: BridgeService) -> None:
        self.service = service
        self.sessions: tuple[AgentSession, ...] = ()
        self.sessions_by_plugin: dict[str, tuple[AgentSession, ...]] = {}
        self._refresh_requested = Event()
        self._logger = logging.getLogger(__name__)

    def refresh(self, output: Mk2DeckOutput) -> None:
        # Push the configured brightness on every refresh.  __enter__ only
        # sets it once at connect time, so without this the dashboard slider
        # has no effect until the Deck reconnects.
        configured = self.service.config.stream_deck.brightness
        self._logger.debug("refresh: pushing brightness=%d to device", configured)
        output.set_brightness(configured)
        snapshots = self.service.snapshots()
        self.sessions_by_plugin = {
            plugin_id: snapshot.sessions for plugin_id, snapshot in snapshots.items()
        }
        self.sessions = self.sessions_by_plugin.get("opencode", ())
        self.service.set_active_snapshots(snapshots)
        # Build span zone lookup: key_index -> parent ButtonBinding
        span_parents: dict[int, ButtonBinding] = {}
        for b in self.service.config.buttons:
            if b.plugin and b.component == "session":
                for i in range(b.key_index, b.key_index + max(b.span, 1)):
                    span_parents[i] = b
        for binding in self.service.config.buttons:
            session = None
            parent = span_parents.get(binding.key_index)
            if parent is not None:
                provider_sessions = self.sessions_by_plugin.get(parent.plugin or "", ())
                # span > 1: sessions auto-assigned by slot, ignore session_id.
                # span = 1: session_id pins to one session; fallback to slot 0.
                if parent.span > 1:
                    slot = binding.key_index - parent.key_index
                    if slot < len(provider_sessions):
                        session = provider_sessions[slot]
                elif parent.session_id:
                    session = next(
                        (s for s in provider_sessions if s.id == parent.session_id),
                        None,
                    )
                elif provider_sessions:
                    session = provider_sessions[0]
            if binding.component == "quota":
                image = render_quota_key(
                    binding,
                    snapshots.get(binding.plugin or ""),
                    size=output.key_size,
                )
            else:
                image = render_control_key(
                    binding,
                    session,
                    selected=(
                        session is not None
                        and parent is not None
                        and session.id == self.service.selected_session_ids.get(parent.plugin or "")
                    ),
                    size=output.key_size,
                    provider_id=parent.plugin if parent is not None else binding.plugin,
                )
            output.set_key(binding.key_index, image)

    def press(self, key_index: int) -> None:
        self.service.press_key(key_index)

    def run(self, *, once: bool = False, sleep: Callable[[float], None] = time.sleep) -> None:
        logger = logging.getLogger(__name__)
        while True:
            try:
                with Mk2DeckOutput(self.service.config.stream_deck) as output:
                    self.service.device_status = {
                        "connected": True,
                        "detail": "MK.2 connected",
                        "key_count": 15,
                    }
                    output.set_key_callback(lambda _deck, key, pressed: self._on_key(key, pressed))
                    while True:
                        self.refresh(output)
                        if once:
                            return
                        self._refresh_requested.wait(
                            self.service.config.bridge.refresh_interval_seconds
                        )
                        self._refresh_requested.clear()
            except DeviceError as exc:
                self.service.device_status = {"connected": False, "detail": str(exc)}
                if once:
                    raise
                logger.error("Stream Deck unavailable: %s", exc)
                sleep(self.service.config.bridge.refresh_interval_seconds)

    def _on_key(self, key_index: int, pressed: bool) -> None:
        if not pressed:
            return
        try:
            self.press(key_index)
        except (BridgeError, OpenCodeError) as exc:
            logging.getLogger(__name__).error("Key %s action failed: %s", key_index, exc)
        except Exception:
            logging.getLogger(__name__).exception("Key %s callback failed", key_index)
        finally:
            # A physical press changes the selected Session. Do not make the
            # corresponding Deck display wait for the polling interval.
            self._refresh_requested.set()
