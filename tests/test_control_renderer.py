from PIL import Image, ImageDraw

from stream_micro.control_config import ButtonBinding
from stream_micro.control_renderer import _font, _wrap_title, render_control_key
from stream_micro.plugins.base import AgentSession, SessionState


def test_control_font_renders_cjk_glyphs_instead_of_missing_glyph_boxes() -> None:
    """A Chinese Session title must not collapse into the font's missing glyph."""

    font = _font(16)
    chinese = Image.new("RGB", (64, 32))
    missing = Image.new("RGB", (64, 32))
    ImageDraw.Draw(chinese).text((0, 0), "中文", fill="white", font=font)
    ImageDraw.Draw(missing).text((0, 0), "\ufffd\ufffd", fill="white", font=font)

    assert chinese.tobytes() != missing.tobytes()


def test_session_key_renders_name_project_folder_and_state() -> None:
    image = render_control_key(
        ButtonBinding(key_index=0, plugin="opencode", component="session", action="select_session"),
        AgentSession(
            "session-1",
            "A deliberately long Section title that must fit",
            SessionState.RUNNING,
            "stream-micro",
        ),
        selected=False,
        size=(96, 96),
    )

    # The three label bands must contain drawn pixels rather than one clipped
    # title line.  Exact glyph comparison would make this font-dependent.
    background = image.getpixel((48, 48))
    assert any(image.getpixel((x, y)) != background for y in range(18, 36) for x in range(8, 88))
    assert any(image.getpixel((x, y)) != background for y in range(40, 58) for x in range(8, 88))
    assert any(image.getpixel((x, y)) != background for y in range(62, 82) for x in range(8, 88))
    assert all(
        image.getpixel((x, y)) != (95, 231, 165)
        for x in range(image.width)
        for y in range(image.height)
    )  # Legacy unbound green frame.


def test_session_title_wraps_to_two_lines_before_truncating() -> None:
    image = Image.new("RGB", (96, 96))
    title = _wrap_title(
        ImageDraw.Draw(image),
        "A deliberately long Section title that must fit",
        _font(11, bold=True),
        84,
    )

    assert title.count("\n") == 1
    assert "Section" in title
