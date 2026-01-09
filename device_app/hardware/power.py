# device_app/hardware/power.py
from __future__ import annotations
import time
from typing import Optional


class DummyPowerManager:
    def get_percent(self) -> int:
        return 100

    def is_low(self) -> bool:
        return False

    def shutdown(self):
        print("[POWER] Dummy shutdown (ignored)")


class PowerManager:
    def __init__(self, cfg: dict):
        self.cfg = cfg
        self._failed = False
        self._initialized = False

        self._ads = None
        self._chan = None

        self.r1 = float(cfg.get("R1", 33000))
        self.r2 = float(cfg.get("R2", 100000))
        self.min_v = 3.2
        self.max_v = 4.2
        self.address = int(str(cfg.get("I2C_ADDRESS", "0x48")), 16)

        self._last_percent = 100

    def _init_adc_once(self):
        if self._initialized or self._failed:
            return

        self._initialized = True
        print("[POWER] Initializing ADS1015 (safe)...")

        try:
            import board, busio
            from adafruit_ads1x15.ads1015 import ADS1015
            from adafruit_ads1x15.analog_in import AnalogIn

            i2c = busio.I2C(board.SCL, board.SDA)
            ads = ADS1015(i2c, address=self.address)
            chan = AnalogIn(ads, 0)

            # test read (CRITICAL)
            _ = chan.voltage

            self._ads = ads
            self._chan = chan
            print("[POWER] ADS1015 ready")

        except Exception as e:
            print("[POWER] ADS1015 init failed → fallback:", e)
            self._failed = True

    def get_percent(self) -> int:
        self._init_adc_once()

        if self._failed or not self._chan:
            return self._last_percent

        try:
            v_adc = self._chan.voltage
            vbat = v_adc * (self.r1 + self.r2) / self.r2
            pct = int(100 * (vbat - self.min_v) / (self.max_v - self.min_v))
            pct = max(0, min(100, pct))
            self._last_percent = pct
            return pct
        except Exception:
            return self._last_percent

    def is_low(self) -> bool:
        return self.get_percent() <= 10

    def shutdown(self):
        print("[POWER] Shutdown requested")
        import os

        os.system("sudo shutdown now")


def create_power_manager(cfg: dict):
    try:
        return PowerManager(cfg.get("POWER", cfg))
    except Exception as e:
        print("[POWER] Fatal error → Dummy:", e)
        return DummyPowerManager()
