from datetime import datetime, timezone

from PIL import Image, ImageDraw

from stream_micro.config import DisplayConfig
from stream_micro.models import QuotaWindow, WindowKind
from stream_micro.renderer import _font, render_error_key, render_quota_key, status_color


def test_status_color_thresholds() -> None:
    config = DisplayConfig()

    assert status_color(69, config) == config.healthy_color
    assert status_color(70, config) == config.warning_color
    assert status_color(90, config) == config.critical_color


def test_renderer_outputs_legible_sized_rgb_image(tmp_path) -> None:
    quota = QuotaWindow(WindowKind.SESSION, 75, datetime(2026, 7, 29, 12, 0, tzinfo=timezone.utc))

    image = render_quota_key(quota, "5H", DisplayConfig(reset_timezone="UTC"), (120, 100))
    path = tmp_path / "key.png"
    image.save(path)

    assert image.mode == "RGB"
    assert image.size == (120, 100)
    with Image.open(path) as saved:
        assert saved.format == "PNG"
        assert len(saved.getcolors(maxcolors=100_000) or []) > 3


def test_quota_renderer_font_renders_the_cjk_glyph_for_display() -> None:
    """The Ollama key must render CJK labels instead of a missing-glyph box."""

    font = _font(16, bold=True)
    cjk = Image.new("RGB", (64, 32))
    missing = Image.new("RGB", (64, 32))
    ImageDraw.Draw(cjk).text((0, 0), "显", fill="white", font=font)
    ImageDraw.Draw(missing).text((0, 0), "\ufffd", fill="white", font=font)

    assert cjk.tobytes() != missing.tobytes()


def test_error_renderer_uses_requested_dimensions() -> None:
    assert render_error_key("expired cookie", DisplayConfig(), (72, 72)).size == (72, 72)
