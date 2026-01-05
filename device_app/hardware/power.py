from __future__ import annotations
import os


class PowerManager:
    """
    Power manager for battery-powered device

    - Read voltage from TP4056 OUT via ADS1015
    - Convert voltage to battery percentage
    - Safe shutdown when battery is low
    """

    def __init__(
        self,
        channel: int = 0,
        r1: int = 100_000,
        r2: int = 100_000,
        low_voltage: float = 3.2,
    ) -> None:
        self.available = False
        self.low_voltage = low_voltage
        self.ratio = (r1 + r2) / r2

        try:
            import board
            import busio
            import adafruit_ads1x15.ads1015 as ADS
            from adafruit_ads1x15.analog_in import AnalogIn

            i2c = busio.I2C(board.SCL, board.SDA)
            ads = ADS.ADS1015(i2c)  # mặc định 0x48
            ads.gain = 1

            self.chan = AnalogIn(ads, getattr(ADS, f"P{channel}"))
            self.available = True

            print("[POWER] ADS1015 detected")

        except Exception as e:
            print(f"[POWER] ADS1015 not available: {e}")
            print("[POWER] Running without battery monitoring")

    # ================= PUBLIC API =================

    def get_voltage(self) -> float:
        if not self.available:
            return 0.0
        return round(self.chan.voltage * self.ratio, 2)

    def get_percent(self) -> int:
        if not self.available:
            return 0

        v = self.get_voltage()
        if v >= 4.2:
            return 100
        if v >= 4.0:
            return 80
        if v >= 3.8:
            return 60
        if v >= 3.7:
            return 50
        if v >= 3.6:
            return 40
        if v >= 3.5:
            return 20
        return 0

    def is_low(self) -> bool:
        if not self.available:
            return False
        return self.get_voltage() <= self.low_voltage

    def shutdown(self) -> None:
        print("[POWER] Shutdown system")
        os.system("sudo shutdown now")


def create_power_manager(config=None) -> PowerManager:
    print("[POWER] Initializing PowerManager")
    return PowerManager()
