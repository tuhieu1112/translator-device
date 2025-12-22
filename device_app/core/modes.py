# device_app/core/modes.py
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto


class Mode(Enum):
    """
    3 chế độ hoạt động:

    - VI_EN : nói tiếng Việt, dịch sang tiếng Anh
    - EN_VI : nói tiếng Anh, dịch sang tiếng Việt
    - EN_EN : nói tiếng Anh, chỉnh / cải thiện câu tiếng Anh
    """

    VI_EN = auto()
    EN_VI = auto()
    EN_EN = auto()

    @property
    def short_label(self) -> str:
        if self is Mode.VI_EN:
            return "VI→EN"
        if self is Mode.EN_VI:
            return "EN→VI"
        if self is Mode.EN_EN:
            return "EN→EN"
        return self.name

    @property
    def description(self) -> str:
        if self is Mode.VI_EN:
            return "Nói tiếng VIỆT, dịch sang tiếng ANH"
        if self is Mode.EN_VI:
            return "Nói tiếng ANH, dịch sang tiếng VIỆT"
        if self is Mode.EN_EN:
            return "Nói tiếng ANH, chỉnh ngữ pháp ANH"
        return self.name

    @classmethod
    def cycle(cls, current: "Mode") -> "Mode":
        """Dùng cho nút đổi chế độ: chuyển sang mode kế tiếp."""
        modes = list(cls)
        idx = modes.index(current)
        return modes[(idx + 1) % len(modes)]


@dataclass
class ModeState:
    """Giữ trạng thái mode hiện tại (dùng cho pipeline / nút bấm)."""

    current: Mode = Mode.EN_VI  # mặc định: nói EN, dịch sang VI

    def next(self) -> Mode:
        self.current = Mode.cycle(self.current)
        return self.current
