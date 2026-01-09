from __future__ import annotations
import time
import os


# ==========================================================
# DUMMY POWER (SAFE FALLBACK)
# ==========================================================
class DummyPowerManager:
    def __init__(self):
        print("[POWER] DummyPowerManager active")

    def get_percent(self) -> int:
        return 100

    def is_low(self) -> bool:
        return False

    def shutdown(self):
        print("[POWER] Dummy shutdown ignored")


# ==========================================================
# REAL POWER (NON-BLOCKING)
# ==========================================================
class PowerManager:
    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.min_v = 3.2
        self.max_v = 4.2
        self.r1 = float(cfg.get("R1", 33000))
        self.r2 = float(cfg.get("R2", 100000))
        self.address = int(str(cfg.get("I2C_ADDRESS", "0x48")), 16)

        self._ads = None
        self._chan = None
        self._last_percent = 100
        self._failed = False

        print("[POWER] PowerManager created (lazy init)")

    def _ensure_adc(self):
        if self._failed or self._ads is not None:
            return

        try:
            import board, busio
            from adafruit_ads1x15.ads1015 import ADS1015
            from adafruit_ads1x15.analog_in import AnalogIn

            print("[POWER] Initializing ADS1015 (lazy)...")

            i2c = busio.I2C(board.SCL, board.SDA)

            t0 = time.time()
            while not i2c.try_lock():
                if time.time() - t0 > 0.5:
                    raise TimeoutError("I2C lock timeout")
                time.sleep(0.01)

            self._ads = ADS1015(i2c, address=self.address)
            self._chan = AnalogIn(self._ads, 0)

            i2c.unlock()
            print("[POWER] ADS1015 ready")

        except Exception as e:
            print("[POWER] ADS1015 failed → disable power:", e)
            self._failed = True

    def get_percent(self) -> int:
        self._ensure_adc()
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
        self._ensure_adc()
        if self._failed or not self._chan:
            return False
        try:
            return self.get_percent() < 10
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
        return PowerManager(cfg.get("POWER", cfg))
    except Exception:
        return DummyPowerManager()
