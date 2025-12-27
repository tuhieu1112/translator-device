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

    # TALK --------------------------------------------------
    def wait_talk(self) -> None:
        input("[DEBUG] Press Enter to TALK...")

    # MODE --------------------------------------------------
    def poll_mode_event(self) -> str | None:
        """
        Debug mode: không có mode vật lý
        return None
        """
        return None


# ==========================================================
# GPIO BUTTONS (Raspberry Pi)
# ==========================================================
class GpioButtons:
    """
    GPIO Buttons:
    - TALK: nhấn giữ để ghi, thả để dừng
    - MODE:
        * nhấn ngắn -> đổi ngôn ngữ
        * giữ lâu   -> shutdown
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

        print(f"[BUTTON] GPIO ready " f"(TALK={self.talk_pin}, MODE={self.mode_pin})")

    # ======================================================
    # TALK (BLOCKING)
    # ======================================================
    def wait_talk(self) -> None:
        """
        BLOCK cho tới khi TALK được nhấn (LOW)
        """
        while GPIO.input(self.talk_pin) == GPIO.HIGH:
            time.sleep(0.01)

        # chờ thả ra (push-to-talk)
        while GPIO.input(self.talk_pin) == GPIO.LOW:
            time.sleep(0.01)

    # ======================================================
    # MODE (NON-BLOCKING, POLL)
    # ======================================================
    def poll_mode_event(self) -> str | None:
        """
        NON-BLOCKING
        return:
          None      : không có sự kiện
          "short"   : nhấn ngắn -> đổi mode
          "long"    : nhấn giữ -> shutdown
        """

        state = GPIO.input(self.mode_pin)

        # MODE vừa được nhấn
        if state == GPIO.LOW and self._mode_pressed_at is None:
            self._mode_pressed_at = time.time()
            return None

        # MODE đang giữ
        if state == GPIO.LOW and self._mode_pressed_at is not None:
            duration = time.time() - self._mode_pressed_at
            if duration >= self.long_press_sec:
                self._mode_pressed_at = None
                return "long"
            return None

        # MODE vừa được thả
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
