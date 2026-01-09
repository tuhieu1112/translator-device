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
        self._released = True

    def wait_talk_press(self) -> None:
        input("[DEBUG] Press Enter to START talking...")
        self._pressed = True
        self._released = False

    def is_talk_pressed(self) -> bool:
        if self._pressed and not self._released:
            time.sleep(0.3)
            self._released = True
            return True
        return False

    def release(self) -> None:
        self._pressed = False
        self._released = True

    def poll_mode_event(self) -> str | None:
        return None


# ==========================================================
# GPIO BUTTONS (Raspberry Pi)
# ==========================================================
class GpioButtons:
    """
    TALK: nhấn giữ để ghi, thả để dừng (pull-up -> pressed == LOW)
    MODE: short press -> đổi mode, long press (>= LONG_PRESS_SEC) -> shutdown
    """

    def __init__(self, cfg: Mapping[str, Any]) -> None:
        if GPIO is None:
            raise RuntimeError("RPi.GPIO is not available")

        buttons_cfg = cfg.get("BUTTONS", {})
        # cho chắc: nếu config đổi thì lấy từ config
        self.talk_pin = int(buttons_cfg.get("TALK_PIN", 17))
        self.mode_pin = int(buttons_cfg.get("MODE_PIN", 27))
        self.long_press_sec = float(buttons_cfg.get("LONG_PRESS_SEC", 5.0))

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.talk_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.mode_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        self._mode_pressed_at: float | None = None
        self._mode_long_reported = False

        # optional: small software debounce
        self._last_mode_state = GPIO.input(self.mode_pin)

        print(f"[BUTTON] GPIO ready (TALK={self.talk_pin}, MODE={self.mode_pin})")

    # ---------------- TALK ----------------
    def wait_talk_press(self) -> None:
        # block until pressed (LOW)
        while GPIO.input(self.talk_pin) == GPIO.HIGH:
            time.sleep(0.01)
        # returned on press

    def is_talk_pressed(self) -> bool:
        # non-blocking check
        return GPIO.input(self.talk_pin) == GPIO.LOW

    # ---------------- MODE ----------------
    def poll_mode_event(self) -> str | None:
        """
        Call often (loop polling). Returns:
         - "short" for short press
         - "long" for long press (single event)
         - None otherwise
        """
        state = GPIO.input(self.mode_pin)  # HIGH when released, LOW when pressed

        # pressed edge
        if state == GPIO.LOW and self._mode_pressed_at is None:
            self._mode_pressed_at = time.time()
            self._mode_long_reported = False
            return None

        # still pressed -> check long press
        if state == GPIO.LOW and self._mode_pressed_at is not None:
            elapsed = time.time() - self._mode_pressed_at
            if (not self._mode_long_reported) and elapsed >= self.long_press_sec:
                # report long once
                self._mode_pressed_at = None
                self._mode_long_reported = True
                return "long"
            return None

        # released after being pressed
        if state == GPIO.HIGH and self._mode_pressed_at is not None:
            duration = time.time() - self._mode_pressed_at
            self._mode_pressed_at = None
            self._mode_long_reported = False
            if duration < self.long_press_sec:
                return "short"
            # if duration >= long_press_sec, long already handled above
            return None

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
