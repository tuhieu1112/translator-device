# device_app/hardware/power.py
from __future__ import annotations

import time
import board
import busio
from adafruit_ads1x15.ads1015 import ADS1015
from adafruit_ads1x15.analog_in import AnalogIn


class PowerManager:
    def __init__(self, config: dict):
        self.r1 = float(config.get("R1", 33000))
        self.r2 = float(config.get("R2", 100000))
        self.min_v = 3.2
        self.max_v = 4.2

        i2c_bus = int(config.get("I2C_BUS", 1))
        address = int(str(config.get("I2C_ADDRESS", "0x48")), 16)

        self.i2c = busio.I2C(board.SCL, board.SDA)
        self.ads = ADS1015(self.i2c, address=address)
        self.chan = AnalogIn(self.ads, 0)  # A0

        self._last_percent = None

        print("[POWER] ADS1015 initialized")

    def read_vbat(self) -> float:
        v_adc = self.chan.voltage
        vbat = v_adc * (self.r1 + self.r2) / self.r2
        return vbat

    def get_percent(self) -> int:
        try:
            vbat = self.read_vbat()
            pct = int(100 * (vbat - self.min_v) / (self.max_v - self.min_v))
            pct = max(0, min(100, pct))
            self._last_percent = pct
            return pct
        except Exception as e:
            print("[POWER] read error:", e)
            return self._last_percent if self._last_percent is not None else 0

    def is_low(self) -> bool:
        try:
            return self.read_vbat() < 3.3
        except Exception:
            return False

    def should_shutdown(self) -> bool:
        try:
            return self.read_vbat() < 3.1
        except Exception:
            return False

    def shutdown(self):
        print("[POWER] Shutdown requested")
        import os

        os.system("sudo shutdown now")
