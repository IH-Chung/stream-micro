from __future__ import annotations

from pathlib import Path

from stream_micro import cli
from stream_micro.control_config import load_control_config


def test_serve_creates_separate_bridge_configuration(tmp_path: Path, monkeypatch) -> None:
    config_path = tmp_path / "bridge.yaml"
    calls: list[tuple[object, str, int]] = []

    def fake_run(application: object, *, host: str, port: int, **_kwargs: object) -> None:
        calls.append((application, host, port))

    monkeypatch.setattr("uvicorn.run", fake_run)
    monkeypatch.setattr(cli.Thread, "start", lambda _thread: None)

    assert cli.main(["serve", "--bridge-config", str(config_path)]) == 0
    assert config_path.exists()
    assert load_control_config(config_path).stream_deck.model == "mk2"
    assert len(calls) == 1
    assert calls[0][1:] == ("127.0.0.1", 8765)


def test_serve_reload_uses_factory_and_watches_python_sources(tmp_path: Path, monkeypatch) -> None:
    config_path = tmp_path / "bridge.yaml"
    calls: list[tuple[object, dict[str, object]]] = []

    def fake_run(application: object, **kwargs: object) -> None:
        calls.append((application, kwargs))

    monkeypatch.setattr("uvicorn.run", fake_run)

    assert cli.main(["serve", "--reload", "--bridge-config", str(config_path)]) == 0
    assert calls == [
        (
            "stream_micro.cli:create_reload_app",
            {
                "factory": True,
                "reload": True,
                "reload_dirs": [str(Path("src").resolve())],
                "host": "127.0.0.1",
                "port": 8765,
            },
        )
    ]
