from __future__ import annotations

import time
from typing import Optional

try:
    import RPi.GPIO as GPIO

    _HAS_GPIO = True
except Exception:
    _HAS_GPIO = False


class GpioButtons:
    """
    SAFE GPIO button backend for Raspberry Pi

    - TALK: press / release
    - MODE: short press / long press
    """

    LONG_PRESS_SEC = 5  # giữ MODE >= 1.2s → shutdown
    DEBOUNCE_SEC = 0.03

    def __init__(self, cfg: dict):
        btn_cfg = cfg.get("BUTTON", {})

        self.talk_pin = int(btn_cfg.get("TALK_GPIO", 17))
        self.mode_pin = int(btn_cfg.get("MODE_GPIO", 27))
        self.active_low = btn_cfg.get("ACTIVE_LOW", True)

        self._talk_last = False
        self._mode_last = False

        self._mode_press_t0: Optional[float] = None
        self._mode_handled = False

        if _HAS_GPIO:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.talk_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.setup(self.mode_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        print(f"[BUTTON] GPIO ready (TALK={self.talk_pin}, MODE={self.mode_pin})")

    # ================= LOW LEVEL =================

    def _read(self, pin: int) -> bool:
        if not _HAS_GPIO:
            return False
        v = GPIO.input(pin)
        return (v == GPIO.LOW) if self.active_low else (v == GPIO.HIGH)

    # ================= TALK =================

    def is_talk_pressed(self) -> bool:
        return self._read(self.talk_pin)

    # ================= MODE =================

    def poll_mode_event(self) -> Optional[str]:
        """
        Non-blocking poll.
        Returns:
            - "short" : short press
            - "long"  : long press
            - None
        """

        now = time.monotonic()
        pressed = self._read(self.mode_pin)

        # ---- edge: pressed ----
        if pressed and not self._mode_last:
            self._mode_press_t0 = now
            self._mode_handled = False

        # ---- holding ----
        if pressed and self._mode_press_t0 and not self._mode_handled:
            if now - self._mode_press_t0 >= self.LONG_PRESS_SEC:
                self._mode_handled = True
                return "long"

        # ---- edge: released ----
        if not pressed and self._mode_last:
            if (
                self._mode_press_t0
                and not self._mode_handled
                and (now - self._mode_press_t0) >= self.DEBOUNCE_SEC
            ):
                return "short"

            self._mode_press_t0 = None
            self._mode_handled = False

        self._mode_last = pressed
        return None


# ================= FACTORY =================


class DebugButtons:
    def poll_mode_event(self):
        return None

    def is_talk_pressed(self):
        return False


def create_buttons(cfg: dict):
    mode = str(cfg.get("BUTTON_MODE", "gpio")).lower()
    if mode == "gpio":
        print("[BUTTON] Using GPIO backend")
        return GpioButtons(cfg)
    print("[BUTTON] Using DEBUG backend")
    return DebugButtons()
