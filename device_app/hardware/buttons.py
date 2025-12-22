# device_app/hardware/buttons.py
from __future__ import annotations

from typing import Any, Mapping
import time

try:
    import RPi.GPIO as GPIO
except Exception:
    GPIO = None


# ==========================================================
#  Backend debug (laptop)
#  - TALK: main sẽ dùng Enter để chạy pipeline (audio sẽ tự giả lập hold)
#  - MODE: debug KHÔNG auto short nữa để tránh đổi mode lung tung
# ==========================================================
class DebugButtons:
    def __init__(self, cfg: Mapping[str, Any]) -> None:
        pass

    # TALK ---------------------------------------------------
    def wait_talk_press(self) -> None:
        # main debug thường tự xử lý Enter, để đây cho tương thích
        input("[DEBUG BUTTON] Nhấn Enter để bắt đầu 1 lượt (TALK)...")

    def is_talk_pressed(self) -> bool:
        return False

    # MODE ---------------------------------------------------
    def wait_mode_short_or_long(self, long_sec: float = 5.0) -> str:
        """
        Debug: không tự trả về 'short' nữa (vì sẽ làm đổi mode liên tục).
        Trả về "" nghĩa là không có sự kiện mode.
        (Nếu muốn mô phỏng, bạn xử lý ở main bằng phím m/p như trước.)
        """
        return ""


# ==========================================================
#  Backend GPIO thật trên Raspberry Pi
# ==========================================================
class GpioButtons:
    """
    Quản lý nút TALK + MODE bằng GPIO.
    - TALK: nhấn giữ để ghi, thả để dừng.
    - MODE: bấm ngắn đổi chế độ, giữ lâu (vd 5s) để tắt máy.
    """

    def __init__(self, cfg: Mapping[str, Any]) -> None:
        if GPIO is None:
            raise RuntimeError("RPi.GPIO không khả dụng trên môi trường hiện tại.")

        buttons_cfg = cfg.get("BUTTONS", {})
        self.talk_pin = int(buttons_cfg.get("TALK_PIN", 23))
        self.mode_pin = int(buttons_cfg.get("MODE_PIN", 24))

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.talk_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.mode_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    # TALK ---------------------------------------------------
    def is_talk_pressed(self) -> bool:
        return GPIO.input(self.talk_pin) == GPIO.LOW

    def wait_talk_press(self) -> None:
        while not self.is_talk_pressed():
            time.sleep(0.01)

    # MODE ---------------------------------------------------
    def wait_mode_short_or_long(self, long_sec: float = 5.0) -> str:
        """
        Chờ 1 lần nhấn MODE (BLOCKING).
        - Nếu nhả ra trước long_sec -> 'short'
        - Nếu giữ ≥ long_sec       -> 'long'
        """
        while GPIO.input(self.mode_pin) == GPIO.HIGH:
            time.sleep(0.01)

        start = time.time()
        while GPIO.input(self.mode_pin) == GPIO.LOW:
            time.sleep(0.01)

        duration = time.time() - start
        return "long" if duration >= long_sec else "short"


def create_buttons(cfg: Mapping[str, Any]):
    mode = str(cfg.get("BUTTON_MODE", "debug")).lower()
    if mode == "gpio":
        print("[BUTTON] Using backend: GPIO")
        return GpioButtons(cfg)
    print("[BUTTON] Using backend: DebugButtons")
    return DebugButtons(cfg)
