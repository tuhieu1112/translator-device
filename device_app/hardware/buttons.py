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
    SAFE GPIO button backend

    - TALK: level-trigger (press / release)
    - MODE:
        * short press  -> toggle mode (ONCE)
        * long press   -> shutdown (>= 5s)
    """

    LONG_PRESS_SEC = 5.0
    DEBOUNCE_SEC = 0.05
    COOLDOWN_SEC = 0.4  # chặn spam mode

    def __init__(self, cfg: dict):
        btn_cfg = cfg.get("BUTTON", {})

        self.talk_pin = int(btn_cfg.get("TALK_GPIO", 17))
        self.mode_pin = int(btn_cfg.get("MODE_GPIO", 27))
        self.active_low = btn_cfg.get("ACTIVE_LOW", True)

        self._mode_last = False
        self._mode_press_t0: Optional[float] = None
        self._mode_handled = False
        self._mode_last_action = 0.0

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
        Edge-triggered, non-blocking.

        Returns:
            - "short" : released before LONG_PRESS_SEC
            - "long"  : pressed >= LONG_PRESS_SEC (ONLY ONCE)
            - None
        """
        now = time.monotonic()
        pressed = self._read(self.mode_pin)

        # ---- pressed edge ----
        if pressed and not self._mode_last:
            self._mode_press_t0 = now
            self._mode_handled = False

        # ---- holding ----
        if (
            pressed
            and self._mode_press_t0
            and not self._mode_handled
            and (now - self._mode_press_t0) >= self.LONG_PRESS_SEC
        ):
            self._mode_handled = True
            return "long"

        # ---- released edge ----
        if not pressed and self._mode_last:
            if (
                self._mode_press_t0
                and not self._mode_handled
                and (now - self._mode_press_t0) >= self.DEBOUNCE_SEC
                and (now - self._mode_last_action) >= self.COOLDOWN_SEC
            ):
                self._mode_last_action = now
                self._mode_press_t0 = None
                return "short"

            self._mode_press_t0 = None
            self._mode_handled = False

        self._mode_last = pressed
        return None


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
