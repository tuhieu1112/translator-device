# device_app/hardware/power.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Optional
import time


# ===== Backend cơ sở =====
@dataclass
class BasePowerBackend:
    def get_battery_percent(self) -> int:
        """
        Trả về % pin (0–100).
        """
        raise NotImplementedError


# ===== Backend debug (chạy trên laptop) =====
class DebugPowerBackend(BasePowerBackend):
    """
    Mô phỏng pin cho khi chạy trên laptop:
    - Bắt đầu 100%
    - Có thể cho tụt rất chậm theo thời gian nếu muốn
    """

    def __init__(self) -> None:
        self._start = time.time()

    def get_battery_percent(self) -> int:
        # Giả lập tụt 1% mỗi 10 phút, nhưng không < 95%
        elapsed = time.time() - self._start
        drain = int(elapsed // 600)  # 600s = 10 phút
        pct = max(100 - drain, 95)
        return pct


# ===== Backend thật cho Raspberry Pi =====
class PiPowerBackend(BasePowerBackend):
    """
    Sau này bạn có thể đọc điện áp từ ADC / IC đo pin.
    Hiện tại tạm trả về 100% để chạy được pipeline.
    """

    def __init__(self, adc_channel: Optional[int] = None) -> None:
        self.adc_channel = adc_channel

    def get_battery_percent(self) -> int:
        # TODO: implement đọc pin thật từ ADC / fuel gauge
        return 100


# ===== Lớp PowerManager mà pipeline.py đang import =====
class PowerManager:
    """
    Quản lý backend pin, chọn theo POWER_MODE trong config.yaml

    POWER_MODE: "debug" hoặc "pi"
    POWER:
      BATTERY_ADC_CH: (tùy chọn) kênh ADC khi dùng trên Pi
    """

    def __init__(self, config: Mapping[str, Any]) -> None:
        power_mode = str(config.get("POWER_MODE", "debug")).lower()
        power_cfg = config.get("POWER", {})

        if power_mode == "pi":
            adc_ch = power_cfg.get("BATTERY_ADC_CH")
            backend: BasePowerBackend = PiPowerBackend(adc_channel=adc_ch)
        else:
            backend = DebugPowerBackend()

        self._backend = backend
        print(f"[POWER] Using backend: {backend.__class__.__name__}")

    def get_battery_percent(self) -> int:
        return self._backend.get_battery_percent()


# ===== Factory cho main.py (để không phải sửa main) =====
def create_power_manager(config: Mapping[str, Any]) -> PowerManager:
    """
    Hàm factory, được main.py import: from device_app.hardware.power import create_power_manager
    """
    return PowerManager(config)
