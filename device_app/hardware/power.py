from __future__ import annotations
import os
import time


class PowerManager:
    """
    Power manager for battery-powered device (Li-Po 3.7V)

    - Read battery voltage from TP4056 OUT+ via ADS1015
    - Convert voltage to battery percentage (UI only)
    - Safe shutdown when battery is critically low
    """

    # ===== Li-Po characteristics =====
    V_FULL = 4.20  # 100%
    V_EMPTY = 3.30  # 0%  (safe lower bound)
    V_LOW = 3.50  # warning
    V_SHUTDOWN = 3.30  # MUST shutdown

    def __init__(
        self,
        channel: int = 0,  # ADS A0
        r1: int = 330_000,  # divider upper resistor
        r2: int = 100_000,  # divider lower resistor
    ) -> None:
        self.available = False
        self.ratio = (r1 + r2) / r2  # = 4.3

        try:
            import board
            import busio
            import adafruit_ads1x15.ads1015 as ADS
            from adafruit_ads1x15.analog_in import AnalogIn

            i2c = busio.I2C(board.SCL, board.SDA)
            ads = ADS.ADS1015(i2c, address=0x48)
            ads.gain = 1

            # ADS1015 channel by index (0 = A0)
            self.chan = AnalogIn(ads, channel)

            self.available = True
            print("[POWER] ADS1015 detected")

        except Exception as e:
            print(f"[POWER] ADS1015 not available: {e}")
            print("[POWER] Running without battery monitoring")

    # ================= PUBLIC API =================

    def get_voltage(self) -> float:
        """
        Real battery voltage (TP4056 OUT+)
        Averaged to reduce noise
        """
        if not self.available:
            return 0.0

        samples = [self.chan.voltage for _ in range(5)]
        avg_ads_v = sum(samples) / len(samples)

        v_bat = avg_ads_v * self.ratio
        return round(v_bat, 2)

    def get_percent(self) -> int:
        """
        Battery percentage (UI purpose only)

        Linear mapping:
        3.30V → 0%
        4.20V → 100%
        """
        if not self.available:
            return 0

        v = self.get_voltage()

        if v >= self.V_FULL:
            return 100
        if v <= self.V_EMPTY:
            return 0

        percent = (v - self.V_EMPTY) / (self.V_FULL - self.V_EMPTY) * 100
        return int(percent)

    def is_low(self) -> bool:
        """
        Battery low warning (notify user)
        """
        if not self.available:
            return False
        return self.get_voltage() <= self.V_LOW

    def should_shutdown(self) -> bool:
        """
        Battery critically low → must shutdown
        """
        if not self.available:
            return False
        return self.get_voltage() <= self.V_SHUTDOWN

    def shutdown(self) -> None:
        """
        Safe system shutdown
        """
        print("[POWER] Battery too low → shutting down")
        time.sleep(1)
        os.system("sudo shutdown now")


def create_power_manager(config=None) -> PowerManager:
    print("[POWER] Initializing PowerManager")
    return PowerManager()
