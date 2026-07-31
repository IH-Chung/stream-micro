"""Small, self-contained visual language for control-surface keys."""

from __future__ import annotations

from PIL import Image, ImageDraw

from .control_config import ButtonBinding
from .plugins.base import AgentSession, SessionState
from .renderer import _font

_STATUS_COLORS = {
    SessionState.IDLE: "#ffffff",
    SessionState.RUNNING: "#4d9de5",
    SessionState.WAITING: "#e5a23b",
    SessionState.COMPLETED: "#4de57a",
    SessionState.ERROR: "#e55d5d",
    SessionState.DISCONNECTED: "#555555",
}


def _fit_text(draw: ImageDraw.ImageDraw, text: str, font, max_width: int) -> str:
    """Fit a single line without letting Stream Deck labels run off the key."""

    if draw.textbbox((0, 0), text, font=font)[2] <= max_width:
        return text
    ellipsis = "…"
    clipped = text
    while clipped and draw.textbbox((0, 0), f"{clipped}{ellipsis}", font=font)[2] > max_width:
        clipped = clipped[:-1]
    return f"{clipped}{ellipsis}" if clipped else ellipsis


def _wrap_title(draw: ImageDraw.ImageDraw, title: str, font, max_width: int) -> str:
    """Fit a Session title on two centred key-display lines.

    Session titles may use words or CJK text, so wrapping by individual
    characters gives both forms a predictable result on the small MK.2 key.
    """

    source = title.strip() or "Untitled session"
    lines: list[str] = []
    line = ""
    for character in source:
        candidate = f"{line}{character}"
        if line and draw.textbbox((0, 0), candidate, font=font)[2] > max_width:
            lines.append(line.rstrip())
            line = character.lstrip()
            if len(lines) == 2:
                break
        else:
            line = candidate
    if len(lines) < 2 and line:
        lines.append(line.rstrip())
    if not lines:
        return "Untitled"
    if len(lines) == 2 and len("".join(lines)) < len(source):
        lines[-1] = _fit_text(draw, f"{lines[-1]}...", font, max_width)
    return "\n".join(lines[:2])


def render_control_key(
    binding: ButtonBinding,
    session: AgentSession | None,
    *,
    selected: bool,
    size: tuple[int, int],
) -> Image.Image:
    background = "#112137" if session else "#101827"
    image = Image.new("RGB", size, background)
    draw = ImageDraw.Draw(image)
    width, height = size
    if session:
        status_color = _STATUS_COLORS.get(session.state, "#ffffff")
        title_font = _font(11, bold=True)
        project_font = _font(9)
        status_font = _font(9, bold=True)
        draw.multiline_text(
            (width // 2, height * 0.27),
            _wrap_title(draw, session.title, title_font, width - 12),
            anchor="mm",
            align="center",
            fill="#ffffff",
            font=title_font,
            spacing=0,
        )
        draw.text(
            (width // 2, height * 0.51),
            _fit_text(draw, session.project or "NO PROJECT", project_font, width - 12),
            anchor="mm",
            fill="#b9c7da",
            font=project_font,
        )
        draw.text(
            (width // 2, height * 0.75),
            session.state.value.upper(),
            anchor="mm",
            fill=status_color,
            font=status_font,
        )
    else:
        label = (binding.component or "empty").replace("_", " ").upper()
        draw.text(
            (width // 2, height * 0.43),
            label,
            anchor="mm",
            align="center",
            fill="#dce6f6",
            font=_font(10, bold=True),
        )
        draw.text(
            (width // 2, height * 0.65),
            f"KEY {binding.key_index + 1}",
            anchor="mm",
            fill="#8292aa",
            font=_font(8),
        )
    if selected:
        draw.rectangle((0, 0, width - 1, height - 1), outline="#ffffff", width=2)
    return image
