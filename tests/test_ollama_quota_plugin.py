from stream_micro.plugins.ollama_quota import OllamaQuotaPlugin


def test_no_cookie_shows_helpful_error() -> None:
    plugin = OllamaQuotaPlugin({"cookie_value": ""})

    snapshot = plugin.snapshot()

    assert snapshot.health.connected is False
    assert "cookie" in snapshot.health.detail.lower()
    assert snapshot.signals == {}
    assert plugin.manifest.actions == ()


def test_unknown_config_key_is_rejected() -> None:
    import pytest

    with pytest.raises(ValueError, match="Unknown"):
        OllamaQuotaPlugin({"unexpected": "value"})


def test_legacy_keys_are_ignored() -> None:
    plugin = OllamaQuotaPlugin({"enabled": True, "legacy_config_path": "config.yaml", "cookie_value": ""})
    snapshot = plugin.snapshot()
    assert snapshot.health.connected is False
    assert "cookie" in snapshot.health.detail.lower()
