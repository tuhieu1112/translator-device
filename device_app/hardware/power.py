# device_app/hardware/power.py
from __future__ import annotations
import time
import os


# ==========================================================
# DUMMY POWER (fallback – NEVER BLOCK)
# ==========================================================
class DummyPowerManager:
    def __init__(self):
        print("[POWER] DummyPowerManager active")

    def get_percent(self) -> int:
        return 100

    def is_low(self) -> bool:
        return False

    def shutdown(self):
        print("[POWER] Dummy shutdown requested (ignored)")


# ==========================================================
# REAL POWER (ADS1015)
# ==========================================================
class PowerManager:
    def __init__(self, cfg: dict):
        self.min_v = 3.2
        self.max_v = 4.2
        self.r1 = float(cfg.get("R1", 33000))
        self.r2 = float(cfg.get("R2", 100000))
        self.address = int(str(cfg.get("I2C_ADDRESS", "0x48")), 16)

        self._last_percent = 100
        self._ads = None
        self._chan = None

        try:
            import board
            import busio
            from adafruit_ads1x15.ads1015 import ADS1015
            from adafruit_ads1x15.analog_in import AnalogIn

            print("[POWER] Initializing ADS1015...")

            self.i2c = busio.I2C(board.SCL, board.SDA)

            # ⚠️ CRITICAL: timeout protection
            t0 = time.time()
            while not self.i2c.try_lock():
                if time.time() - t0 > 1.0:
                    raise TimeoutError("I2C lock timeout")
                time.sleep(0.01)

            self._ads = ADS1015(self.i2c, address=self.address)
            self._chan = AnalogIn(self._ads, 0)

            self.i2c.unlock()

            print("[POWER] ADS1015 ready")

        except Exception as e:
            print("[POWER] Init failed → fallback DummyPowerManager:", e)
            raise

    def read_vbat(self) -> float:
        v_adc = self._chan.voltage
        return v_adc * (self.r1 + self.r2) / self.r2

    def get_percent(self) -> int:
        try:
            v = self.read_vbat()
            pct = int(100 * (v - self.min_v) / (self.max_v - self.min_v))
            pct = max(0, min(100, pct))
            self._last_percent = pct
            return pct
        except Exception:
            return self._last_percent

    def is_low(self) -> bool:
        try:
            return self.read_vbat() < 3.3
        except Exception:
            return False

    def shutdown(self):
        print("[POWER] Shutdown requested")
        os.system("sudo shutdown now")


# ==========================================================
# FACTORY (ABSOLUTELY SAFE)
# ==========================================================
def create_power_manager(cfg: dict):
    try:
        power_cfg = cfg.get("POWER", cfg)
        return PowerManager(power_cfg)
    except Exception:
        return DummyPowerManager()
