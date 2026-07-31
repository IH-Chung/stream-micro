from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class WindowKind(str, Enum):
    SESSION = "session"
    WEEKLY = "weekly"


@dataclass(frozen=True)
class QuotaWindow:
    kind: WindowKind
    percent_used: float
    reset_at: datetime | None = None

    def __post_init__(self) -> None:
        if not 0 <= self.percent_used <= 100:
            raise ValueError("percent_used must be between 0 and 100")


@dataclass(frozen=True)
class QuotaSnapshot:
    session: QuotaWindow
    weekly: QuotaWindow
