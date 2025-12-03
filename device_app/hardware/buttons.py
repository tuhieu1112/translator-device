# device_app/hardware/buttons.py

"""
Lớp Buttons sẽ có 2 nhiệm vụ:

- Chờ người dùng giữ nút TALK, nhả ra → trả về "một lượt thu âm".
- Theo dõi nút MODE/POWER:
    + Nhấn ngắn: đổi chế độ ngôn ngữ.
    + Nhấn dài >= LONG_PRESS_SEC: yêu cầu shutdown.

Trên PC, ta dùng bản Debug (giả lập bằng input()).
Trên Pi, ta sẽ dùng GPIO thật.
"""

from dataclasses import dataclass

LONG_PRESS_SEC = 5  # giữ 5s để shutdown


@dataclass
class ButtonEvent:
    """Kết quả đọc nút mode/power."""
    shutdown: bool = False
    toggle_mode: bool = False


class BaseButtons:
    def wait_talk_cycle(self):
        """
        Blocking đến khi người dùng 'giữ & nhả' nút TALK.
        Trên Pi: chờ GPIO từ HIGH->LOW, v.v.
        Trả về None, chỉ dùng để báo pipeline bắt đầu thu âm.
        """
        raise NotImplementedError

    def check_mode_or_shutdown(self) -> ButtonEvent:
        """
        Không blocking lâu, gọi lặp lại trong vòng lặp chính.

        - Nếu phát hiện nhấn ngắn nút 2: trả về ButtonEvent(toggle_mode=True).
        - Nếu phát hiện giữ >= LONG_PRESS_SEC: trả về ButtonEvent(shutdown=True).
        """
        raise NotImplementedError


class DebugButtons(BaseButtons):
    """
    Bản debug dùng trên PC: thao tác bằng bàn phím / input().
    Đủ để bạn demo luồng logic mà không cần GPIO thật.
    """

    def wait_talk_cycle(self):
        input("Nhấn Enter để GIẢ LẬP: giữ & nhả nút TALK (bắt đầu thu/dịch)...")

    def check_mode_or_shutdown(self) -> ButtonEvent:
        # Bản demo đơn giản: hỏi người dùng muốn làm gì
        # (Gọi hàm này trong vòng lặp chính, nhưng chỉ demo thôi.)
        return ButtonEvent(toggle_mode=False, shutdown=False)


class GPIOButtons(BaseButtons):
    """
    Bản thật dùng trên Raspberry Pi (RPi.GPIO/gpiozero).
    Hiện tại để TODO.
    """

    def __init__(self, config):
        self.config = config
        # TODO: đọc số chân GPIO từ config, setup GPIO mode,...

    def wait_talk_cycle(self):
        # TODO: chờ cạnh nhấn & nhả trên chân TALK_BUTTON
        pass

    def check_mode_or_shutdown(self) -> ButtonEvent:
        # TODO: đo thời gian giữ nút MODE/POWER để phân biệt ngắn/dài
        return ButtonEvent()
        

def create_buttons(config) -> BaseButtons:
    mode = config.get("BUTTON_MODE", "debug")
    if mode == "gpio":
        return GPIOButtons(config)
    return DebugButtons()
