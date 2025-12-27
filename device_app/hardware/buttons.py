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
        self._pressed = False

    # ---------------- TALK ----------------
    def wait_talk_press(self) -> None:
        input("[DEBUG] Press Enter to START talking...")
        self._pressed = True

    def is_talk_pressed(self) -> bool:
        # Debug: coi như đang giữ cho tới khi stop_record
        return self._pressed

    def release(self) -> None:
        self._pressed = False

    # ---------------- MODE ----------------
    def poll_mode_event(self) -> str | None:
        return None


# ==========================================================
# GPIO BUTTONS (Raspberry Pi)
# ==========================================================
class GpioButtons:
    """
    GPIO Buttons:
    - TALK: nhấn giữ để ghi, thả để dừng
    - MODE:
        * short press -> đổi ngôn ngữ
        * long press  -> shutdown
    """

    def __init__(self, cfg: Mapping[str, Any]) -> None:
        if GPIO is None:
            raise RuntimeError("RPi.GPIO is not available")

        buttons_cfg = cfg.get("BUTTONS", {})
        self.talk_pin = int(buttons_cfg.get("TALK_PIN", 23))
        self.mode_pin = int(buttons_cfg.get("MODE_PIN", 24))
        self.long_press_sec = float(buttons_cfg.get("LONG_PRESS_SEC", 5.0))

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.talk_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.mode_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        self._mode_pressed_at: float | None = None

        print(f"[BUTTON] GPIO ready (TALK={self.talk_pin}, MODE={self.mode_pin})")

    # ---------------- TALK ----------------
    def wait_talk_press(self) -> None:
        while GPIO.input(self.talk_pin) == GPIO.HIGH:
            time.sleep(0.01)

    def is_talk_pressed(self) -> bool:
        return GPIO.input(self.talk_pin) == GPIO.LOW

    # ---------------- MODE ----------------
    def poll_mode_event(self) -> str | None:
        state = GPIO.input(self.mode_pin)

        if state == GPIO.LOW and self._mode_pressed_at is None:
            self._mode_pressed_at = time.time()
            return None

        if state == GPIO.LOW and self._mode_pressed_at is not None:
            if time.time() - self._mode_pressed_at >= self.long_press_sec:
                self._mode_pressed_at = None
                return "long"

        if state == GPIO.HIGH and self._mode_pressed_at is not None:
            duration = time.time() - self._mode_pressed_at
            self._mode_pressed_at = None
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
