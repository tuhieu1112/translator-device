# device_app/core/modes.py
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto


class Mode(Enum):
    """
    2 chế độ hoạt động:

    - VI_EN : nói tiếng Việt, dịch sang tiếng Anh
    - EN_VI : nói tiếng Anh, dịch sang tiếng Việt
    """

    VI_EN = auto()
    EN_VI = auto()

    @property
    def short_label(self) -> str:
        if self is Mode.VI_EN:
            return "VI→EN"
        if self is Mode.EN_VI:
            return "EN→VI"
        return self.name

    @property
    def description(self) -> str:
        if self is Mode.VI_EN:
            return "Nói tiếng VIỆT, dịch sang tiếng ANH"
        if self is Mode.EN_VI:
            return "Nói tiếng ANH, dịch sang tiếng VIỆT"
        return self.name

    @classmethod
    def cycle(cls, current: "Mode") -> "Mode":
        """Dùng cho nút MODE: chuyển qua lại giữa VI_EN ↔ EN_VI."""
        return Mode.EN_VI if current is Mode.VI_EN else Mode.VI_EN


@dataclass
class ModeState:
    """
    Giữ trạng thái mode hiện tại
    (dùng cho pipeline + button + display)
    """

    current: Mode = Mode.EN_VI  # mặc định: EN → VI

    def next(self) -> Mode:
        self.current = Mode.cycle(self.current)
        return self.current
