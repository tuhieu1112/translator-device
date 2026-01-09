from __future__ import annotations
from typing import Any, Mapping
import time

try:
    import RPi.GPIO as GPIO
except Exception:
    GPIO = None


# ==========================================================
# DEBUG BUTTONS (Laptop / VS Code)
# ==========================================================
class DebugButtons:
    def __init__(self, cfg: Mapping[str, Any]) -> None:
        pass

    def is_talk_pressed(self) -> bool:
        return False

    def poll_mode_event(self) -> str | None:
        return None


# ==========================================================
# GPIO BUTTONS (Raspberry Pi)
# ==========================================================
class GpioButtons:
    """
    GPIO Buttons (REAL HARDWARE)

    - TALK (GPIO xx):
        * nhấn giữ -> ghi âm
        * thả      -> dừng ghi

    - MODE (GPIO yy):
        * short press (< LONG_PRESS_SEC) -> đổi mode
        * long press  (>= LONG_PRESS_SEC) -> shutdown
    """

    def __init__(self, cfg: Mapping[str, Any]) -> None:
        if GPIO is None:
            raise RuntimeError("RPi.GPIO not available")

        buttons_cfg = cfg.get("BUTTONS", {})
        self.talk_pin = int(buttons_cfg.get("TALK_PIN", 17))
        self.mode_pin = int(buttons_cfg.get("MODE_PIN", 27))
        self.long_press_sec = float(buttons_cfg.get("LONG_PRESS_SEC", 5.0))

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.talk_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.mode_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        self._mode_pressed_at: float | None = None
        self._last_mode_event_at: float = 0.0  # debounce

        print(f"[BUTTON] GPIO ready (TALK={self.talk_pin}, MODE={self.mode_pin})")

    # ---------------- TALK ----------------
    def is_talk_pressed(self) -> bool:
        # Active LOW (nút nối GND)
        return GPIO.input(self.talk_pin) == GPIO.LOW

    # ---------------- MODE ----------------
    def poll_mode_event(self) -> str | None:
        now = time.time()
        state = GPIO.input(self.mode_pin)

        # debounce: không cho spam event
        if now - self._last_mode_event_at < 0.2:
            return None

        # vừa nhấn
        if state == GPIO.LOW and self._mode_pressed_at is None:
            self._mode_pressed_at = now
            return None

        # đang giữ
        if state == GPIO.LOW and self._mode_pressed_at is not None:
            if now - self._mode_pressed_at >= self.long_press_sec:
                self._mode_pressed_at = None
                self._last_mode_event_at = now
                return "long"

        # thả nút
        if state == GPIO.HIGH and self._mode_pressed_at is not None:
            duration = now - self._mode_pressed_at
            self._mode_pressed_at = None
            self._last_mode_event_at = now

            if duration < self.long_press_sec:
                return "short"

        return None


# ==========================================================
# FACTORY
# ==========================================================
def create_buttons(cfg: Mapping[str, Any]):
    mode = str(cfg.get("BUTTON_MODE", "debug")).lower()

    if mode == "gpio":
        print("[BUTTON] Using GPIO backend")
        return GpioButtons(cfg)

    print("[BUTTON] Using Debug backend")
    return DebugButtons(cfg)
