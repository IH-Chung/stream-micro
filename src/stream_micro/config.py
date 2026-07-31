from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import yaml


class ConfigError(ValueError):
    """Raised when configuration is missing or invalid."""


@dataclass(frozen=True)
class OllamaConfig:
    settings_url: str = "https://ollama.com/settings"
    cookie_name: str = "__Secure-session"
    cookie_value: str = ""
    request_timeout_seconds: float = 15.0
    refresh_interval_seconds: float = 60.0


@dataclass(frozen=True)
class StreamDeckConfig:
    device_serial: str | None = None
    session_key_index: int = 0
    weekly_key_index: int = 1
    brightness: int = 40
    reset_on_start: bool = False
    reset_on_exit: bool = False


@dataclass(frozen=True)
class DisplayConfig:
    healthy_color: str = "#22c55e"
    warning_color: str = "#f59e0b"
    critical_color: str = "#ef4444"
    error_color: str = "#dc2626"
    background_color: str = "#0b1020"
    text_color: str = "#ffffff"
    warning_threshold: int = 70
    critical_threshold: int = 90
    reset_timezone: str = "local"


@dataclass(frozen=True)
class LoggingConfig:
    level: str = "INFO"


@dataclass(frozen=True)
class AppConfig:
    ollama: OllamaConfig
    stream_deck: StreamDeckConfig
    display: DisplayConfig
    logging: LoggingConfig


PLACEHOLDER_MARKERS = ("placeholder", "paste_cookie", "paste-cookie", "changeme", "your_cookie")
LOG_LEVELS = {"CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "NOTSET"}


def _section(data: dict[str, Any], name: str) -> dict[str, Any]:
    value = data.get(name, {})
    if not isinstance(value, dict):
        raise ConfigError(f"'{name}' must be a YAML mapping")
    return value


def _construct(cls: type[Any], values: dict[str, Any], section_name: str) -> Any:
    fields = cls.__dataclass_fields__
    unknown = sorted(set(values) - set(fields))
    if unknown:
        raise ConfigError(f"Unknown setting(s) in '{section_name}': {', '.join(unknown)}")
    try:
        return cls(**values)
    except TypeError as exc:
        raise ConfigError(f"Invalid '{section_name}' settings: {exc}") from exc


def load_config(path: Path | str, *, demo: bool = False) -> AppConfig:
    config_path = Path(path)
    if not config_path.exists():
        if demo:
            data: dict[str, Any] = {}
        else:
            raise ConfigError(
                f"Configuration file not found: {config_path}. "
                "Copy config.example.yaml to config.yaml and set the cookie value."
            )
    else:
        try:
            raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            raise ConfigError(f"Invalid YAML in {config_path}: {exc}") from exc
        if raw is None:
            data = {}
        elif isinstance(raw, dict):
            data = raw
        else:
            raise ConfigError("The YAML document root must be a mapping")

    unknown_sections = sorted(set(data) - {"ollama", "stream_deck", "display", "logging"})
    if unknown_sections:
        raise ConfigError(f"Unknown configuration section(s): {', '.join(unknown_sections)}")

    config = AppConfig(
        ollama=_construct(OllamaConfig, _section(data, "ollama"), "ollama"),
        stream_deck=_construct(StreamDeckConfig, _section(data, "stream_deck"), "stream_deck"),
        display=_construct(DisplayConfig, _section(data, "display"), "display"),
        logging=_construct(LoggingConfig, _section(data, "logging"), "logging"),
    )
    validate_config(config, demo=demo)
    return config


def validate_config(config: AppConfig, *, demo: bool = False) -> None:
    numeric_settings = (
        ("ollama.request_timeout_seconds", config.ollama.request_timeout_seconds),
        ("ollama.refresh_interval_seconds", config.ollama.refresh_interval_seconds),
        ("stream_deck.session_key_index", config.stream_deck.session_key_index),
        ("stream_deck.weekly_key_index", config.stream_deck.weekly_key_index),
        ("stream_deck.brightness", config.stream_deck.brightness),
        ("display.warning_threshold", config.display.warning_threshold),
        ("display.critical_threshold", config.display.critical_threshold),
    )
    for name, value in numeric_settings:
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise ConfigError(f"{name} must be a number")
    integer_settings = (
        ("stream_deck.session_key_index", config.stream_deck.session_key_index),
        ("stream_deck.weekly_key_index", config.stream_deck.weekly_key_index),
        ("stream_deck.brightness", config.stream_deck.brightness),
        ("display.warning_threshold", config.display.warning_threshold),
        ("display.critical_threshold", config.display.critical_threshold),
    )
    for name, value in integer_settings:
        if not isinstance(value, int) or isinstance(value, bool):
            raise ConfigError(f"{name} must be an integer")
    string_settings = (
        ("ollama.settings_url", config.ollama.settings_url),
        ("ollama.cookie_name", config.ollama.cookie_name),
        ("ollama.cookie_value", config.ollama.cookie_value),
        ("display.reset_timezone", config.display.reset_timezone),
        ("logging.level", config.logging.level),
    )
    for name, value in string_settings:
        if not isinstance(value, str):
            raise ConfigError(f"{name} must be a string")
    boolean_settings = (
        ("stream_deck.reset_on_start", config.stream_deck.reset_on_start),
        ("stream_deck.reset_on_exit", config.stream_deck.reset_on_exit),
    )
    for name, value in boolean_settings:
        if not isinstance(value, bool):
            raise ConfigError(f"{name} must be true or false")
    serial = config.stream_deck.device_serial
    if serial is not None and (not isinstance(serial, str) or not serial.strip()):
        raise ConfigError("stream_deck.device_serial must be a non-empty string or null")
    parsed_url = urlparse(config.ollama.settings_url)
    if (
        parsed_url.scheme != "https"
        or parsed_url.hostname != "ollama.com"
        or parsed_url.username is not None
        or parsed_url.password is not None
    ):
        raise ConfigError(
            "ollama.settings_url must be an HTTPS URL on ollama.com without credentials"
        )
    if not config.ollama.cookie_name.strip():
        raise ConfigError("ollama.cookie_name must not be empty")
    cookie = config.ollama.cookie_value.strip()
    if not demo and (not cookie or any(marker in cookie.lower() for marker in PLACEHOLDER_MARKERS)):
        raise ConfigError(
            "ollama.cookie_value is empty or still a placeholder; paste only the cookie value"
        )
    if config.ollama.request_timeout_seconds <= 0:
        raise ConfigError("ollama.request_timeout_seconds must be greater than 0")
    if config.ollama.refresh_interval_seconds <= 0:
        raise ConfigError("ollama.refresh_interval_seconds must be greater than 0")
    deck = config.stream_deck
    if deck.session_key_index < 0 or deck.weekly_key_index < 0:
        raise ConfigError("Stream Deck key indices must be zero or greater")
    if deck.session_key_index == deck.weekly_key_index:
        raise ConfigError("Session and weekly key indices must be different")
    if not 0 <= deck.brightness <= 100:
        raise ConfigError("stream_deck.brightness must be between 0 and 100")
    display = config.display
    if not 0 <= display.warning_threshold < display.critical_threshold <= 100:
        raise ConfigError(
            "display thresholds must satisfy 0 <= warning_threshold < critical_threshold <= 100"
        )
    for name in (
        "healthy_color",
        "warning_color",
        "critical_color",
        "error_color",
        "background_color",
        "text_color",
    ):
        value = getattr(display, name)
        if not isinstance(value, str) or len(value) != 7 or not value.startswith("#"):
            raise ConfigError(f"display.{name} must be a #RRGGBB color")
        try:
            int(value[1:], 16)
        except ValueError as exc:
            raise ConfigError(f"display.{name} must be a #RRGGBB color") from exc
    if config.display.reset_timezone.lower() != "local":
        try:
            ZoneInfo(config.display.reset_timezone)
        except ZoneInfoNotFoundError as exc:
            raise ConfigError(
                "display.reset_timezone must be 'local' or a valid IANA timezone"
            ) from exc
    if config.logging.level.upper() not in LOG_LEVELS:
        raise ConfigError(f"Unknown logging.level: {config.logging.level}")
