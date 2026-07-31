"""Display-only adapter for the existing Ollama quota scraper."""

from __future__ import annotations

from typing import Any

from ..config import OllamaConfig
from ..scraper import ScrapeError, fetch_quota
from .base import PluginHealth, PluginManifest, PluginSnapshot

DEFAULT_SETTINGS_URL = "https://ollama.com/settings"
DEFAULT_COOKIE_NAME = "__Secure-session"
DEFAULT_REQUEST_TIMEOUT = 15.0
DEFAULT_REFRESH_INTERVAL = 60.0

_ALLOWED_KEYS = frozenset(
    {
        "cookie_value",
        "settings_url",
        "cookie_name",
        "request_timeout_seconds",
        "refresh_interval_seconds",
    }
)
_IGNORED_LEGACY_KEYS = frozenset({"enabled", "legacy_config_path"})


class OllamaQuotaPlugin:
    manifest = PluginManifest(
        id="ollama_quota",
        name="Ollama quota",
        components=("quota",),
        actions=(),
    )

    def __init__(self, config: dict[str, Any]) -> None:
        self.validate_config(config)
        self.config = config

    def validate_config(self, config: dict[str, Any]) -> None:
        if not isinstance(config, dict):
            raise ValueError("ollama_quota config must be a mapping")
        unknown = sorted(set(config) - _ALLOWED_KEYS - _IGNORED_LEGACY_KEYS)
        if unknown:
            raise ValueError(f"Unknown ollama_quota setting(s): {', '.join(unknown)}")
        if not isinstance(config.get("cookie_value", ""), str):
            raise ValueError("ollama_quota.cookie_value must be a string")
        url = config.get("settings_url", DEFAULT_SETTINGS_URL)
        if not isinstance(url, str) or not url:
            raise ValueError("ollama_quota.settings_url must be a non-empty string")
        name = config.get("cookie_name", DEFAULT_COOKIE_NAME)
        if not isinstance(name, str) or not name:
            raise ValueError("ollama_quota.cookie_name must be a non-empty string")
        timeout = config.get("request_timeout_seconds", DEFAULT_REQUEST_TIMEOUT)
        if not isinstance(timeout, (int, float)) or isinstance(timeout, bool) or timeout <= 0:
            raise ValueError("ollama_quota.request_timeout_seconds must be a positive number")
        interval = config.get("refresh_interval_seconds", DEFAULT_REFRESH_INTERVAL)
        if not isinstance(interval, (int, float)) or isinstance(interval, bool) or interval <= 0:
            raise ValueError("ollama_quota.refresh_interval_seconds must be a positive number")

    def _build_ollama_config(self) -> OllamaConfig:
        return OllamaConfig(
            settings_url=self.config.get("settings_url", DEFAULT_SETTINGS_URL),
            cookie_name=self.config.get("cookie_name", DEFAULT_COOKIE_NAME),
            cookie_value=self.config.get("cookie_value", ""),
            request_timeout_seconds=self.config.get(
                "request_timeout_seconds", DEFAULT_REQUEST_TIMEOUT
            ),
            refresh_interval_seconds=self.config.get(
                "refresh_interval_seconds", DEFAULT_REFRESH_INTERVAL
            ),
        )

    def snapshot(self) -> PluginSnapshot:
        if not self.config.get("cookie_value", "").strip():
            return PluginSnapshot(
                PluginHealth(False, "No cookie value configured"),
                signals={},
            )
        try:
            quota = fetch_quota(self._build_ollama_config())
        except ScrapeError as exc:
            return PluginSnapshot(PluginHealth(False, str(exc)), signals={})
        return PluginSnapshot(
            PluginHealth(True, "Connected"),
            signals={
                "session_percent": quota.session.percent_used,
                "weekly_percent": quota.weekly.percent_used,
                "session_reset_at": quota.session.reset_at.isoformat()
                if quota.session.reset_at
                else None,
                "weekly_reset_at": quota.weekly.reset_at.isoformat()
                if quota.weekly.reset_at
                else None,
            },
        )

    def invoke(self, action: str, params: dict[str, Any]) -> Any:
        raise ValueError("Ollama quota is display-only")
