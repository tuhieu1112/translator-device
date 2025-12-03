# device_app/hardware/display.py

from abc import ABC, abstractmethod
from typing import Optional


class BaseDisplay(ABC):
    """Interface chung cho màn hình hiển thị."""

    @abstractmethod
    def show_status(self, line1: str, line2: str = "", battery: Optional[int] = None):
        """Hiển thị 2 dòng trạng thái + (tuỳ chọn) % pin."""
        raise NotImplementedError

    @abstractmethod
    def clear(self):
        raise NotImplementedError


class DebugDisplay(BaseDisplay):
    """
    Dùng khi chạy trên PC / VS Code:
    chỉ in ra terminal để demo nội dung OLED.
    """

    def show_status(self, line1: str, line2: str = "", battery: Optional[int] = None):
        parts = [f"[OLED DEBUG] {line1}"]
        if line2:
            parts.append(f" | {line2}")
        if battery is not None:
            parts.append(f" | Battery: {battery}%")
        print("".join(parts))

    def clear(self):
        print("[OLED DEBUG] clear")


class OledDisplay(BaseDisplay):
    """
    Dùng trên Raspberry Pi, nối với OLED thật (I2C).
    Hiện tại để TODO, sau này bạn thêm code thư viện OLED vào.
    """

    def __init__(self, config):
        self.config = config
        # TODO: khởi tạo thư viện OLED, ví dụ luma.oled hoặc adafruit_ssd1306
        # self.device = ...

    def show_status(self, line1: str, line2: str = "", battery: Optional[int] = None):
        # TODO: vẽ 2 dòng + mức pin lên OLED thật
        # ví dụ: clear → vẽ text
        pass

    def clear(self):
        # TODO: clear màn hình
        pass


def create_display(config) -> BaseDisplay:
    mode = config.get("DISPLAY_MODE", "debug")
    if mode == "oled":
        return OledDisplay(config)
    return DebugDisplay()
