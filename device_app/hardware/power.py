# device_app/hardware/power.py
from __future__ import annotations

import time
from typing import Optional


# ============================================================
# DUMMY POWER (fallback – luôn hoạt động)
# ============================================================
class DummyPowerManager:
    def __init__(self):
        self._percent = None
        print("[POWER] DummyPowerManager active")

    def get_percent(self) -> Optional[int]:
        return self._percent

    def is_low(self) -> bool:
        return False

    def should_shutdown(self) -> bool:
        return False

    def shutdown(self):
        print("[POWER] Shutdown requested (dummy – ignored)")


# ============================================================
# REAL POWER MANAGER (ADS1015)
# ============================================================
class PowerManager:
    def __init__(self, cfg: dict):
        # -------- CONFIG --------
        self.r1 = float(cfg.get("R1", 33000))
        self.r2 = float(cfg.get("R2", 100000))
        self.min_v = float(cfg.get("MIN_V", 3.2))
        self.max_v = float(cfg.get("MAX_V", 4.2))

        addr_raw = cfg.get("I2C_ADDRESS", "0x48")
        self.address = int(str(addr_raw), 16)

        self._last_percent: Optional[int] = None

        # -------- SAFE IMPORT --------
        try:
            import board
            import busio
            from adafruit_ads1x15.ads1015 import ADS1015
            from adafruit_ads1x15.analog_in import AnalogIn
        except Exception as e:
            raise RuntimeError(f"ADS1015 import failed: {e}")

        # -------- SAFE I2C INIT (NON-BLOCKING) --------
        try:
            self.i2c = busio.I2C(board.SCL, board.SDA)
            t0 = time.time()
            while not self.i2c.try_lock():
                if time.time() - t0 > 1.0:
                    raise TimeoutError("I2C lock timeout")
                time.sleep(0.01)

            self.ads = ADS1015(self.i2c, address=self.address)
            self.chan = AnalogIn(self.ads, 0)  # A0
            self.i2c.unlock()

        except Exception as e:
            raise RuntimeError(f"ADS1015 init failed: {e}")

        print("[POWER] ADS1015 initialized")

    # ---------------- INTERNAL ----------------
    def _read_vbat(self) -> float:
        v_adc = float(self.chan.voltage)
        return v_adc * (self.r1 + self.r2) / self.r2

    # ---------------- PUBLIC API ----------------
    def get_percent(self) -> Optional[int]:
        try:
            v = self._read_vbat()
            pct = int(100 * (v - self.min_v) / (self.max_v - self.min_v))
            pct = max(0, min(100, pct))
            self._last_percent = pct
            return pct
        except Exception as e:
            print("[POWER] Read error:", e)
            return self._last_percent

    def is_low(self) -> bool:
        try:
            return self._read_vbat() < 3.3
        except Exception:
            return False

    def should_shutdown(self) -> bool:
        try:
            return self._read_vbat() < 3.1
        except Exception:
            return False

    def shutdown(self):
        print("[POWER] Shutdown requested")
        try:
            import os

            os.system("sudo shutdown now")
        except Exception as e:
            print("[POWER] Shutdown failed:", e)


# ============================================================
# FACTORY (KHÔNG BAO GIỜ FAIL)
# ============================================================
def create_power_manager(cfg: dict):
    try:
        power_cfg = cfg.get("POWER", cfg)
        return PowerManager(power_cfg)
    except Exception as e:
        print("[POWER] Init failed → Dummy fallback:", e)
        return DummyPowerManager()
