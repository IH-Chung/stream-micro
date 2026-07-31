from pathlib import Path

import pytest

from stream_micro.config import ConfigError, load_config


def write_config(tmp_path: Path, body: str) -> Path:
    path = tmp_path / "config.yaml"
    path.write_text(body, encoding="utf-8")
    return path


def test_load_config_applies_defaults_and_accepts_real_cookie(tmp_path: Path) -> None:
    path = write_config(tmp_path, "ollama:\n  cookie_value: secret-session-value\n")

    config = load_config(path)

    assert config.ollama.cookie_name == "__Secure-session"
    assert config.stream_deck.session_key_index == 0
    assert config.stream_deck.weekly_key_index == 1
    assert config.stream_deck.reset_on_start is False
    assert config.display.warning_threshold == 70


def test_normal_mode_rejects_placeholder_cookie(tmp_path: Path) -> None:
    path = write_config(tmp_path, "ollama:\n  cookie_value: PASTE_COOKIE_VALUE_HERE\n")

    with pytest.raises(ConfigError, match="paste only the cookie value"):
        load_config(path)


def test_demo_mode_allows_missing_config_and_cookie(tmp_path: Path) -> None:
    config = load_config(tmp_path / "missing.yaml", demo=True)

    assert config.ollama.cookie_value == ""


@pytest.mark.parametrize(
    ("body", "message"),
    [
        (
            "ollama:\n  cookie_value: x\ndisplay:\n  warning_threshold: 90\n"
            "  critical_threshold: 80\n",
            "thresholds",
        ),
        (
            "ollama:\n  cookie_value: x\nstream_deck:\n  session_key_index: 1\n"
            "  weekly_key_index: 1\n",
            "must be different",
        ),
        ("ollama:\n  cookie_value: x\nstream_deck:\n  brightness: 101\n", "brightness"),
        (
            "ollama:\n  cookie_value: x\n  refresh_interval_seconds: often\n",
            "must be a number",
        ),
        (
            "ollama:\n  settings_url: http://ollama.com/settings\n  cookie_value: x\n",
            "HTTPS URL on ollama.com",
        ),
        (
            "ollama:\n  settings_url: https://example.com/settings\n  cookie_value: x\n",
            "HTTPS URL on ollama.com",
        ),
        (
            "ollama:\n  cookie_value: x\nstream_deck:\n  device_serial: 123\n",
            "non-empty string or null",
        ),
        (
            "ollama:\n  cookie_value: x\nstream_deck:\n  device_serial: ''\n",
            "non-empty string or null",
        ),
        (
            "ollama:\n  cookie_value: x\nstream_deck:\n  session_key_index: true\n",
            "must be a number",
        ),
        (
            "ollama:\n  cookie_value: x\nstream_deck:\n  weekly_key_index: 1.5\n",
            "must be an integer",
        ),
        (
            "ollama:\n  cookie_value: x\ndisplay:\n  reset_timezone: Mars/Olympus\n",
            "valid IANA timezone",
        ),
        ("ollama:\n  cookie_value: x\ndisplay:\n  healthy_color: green\n", "#RRGGBB"),
    ],
)
def test_invalid_config_has_actionable_error(tmp_path: Path, body: str, message: str) -> None:
    with pytest.raises(ConfigError, match=message):
        load_config(write_config(tmp_path, body))
