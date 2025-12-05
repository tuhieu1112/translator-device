# device_app/main.py

from device_app.utils.config import load_config
from device_app.hardware.display import create_display
from device_app.hardware.buttons import create_buttons
from device_app.hardware.power import create_power
from device_app.hardware.audio import create_audio
from device_app.core.pipeline import TranslatorPipeline


# 3 chế độ xoay vòng bằng nút MODE
MODES = ["VI→EN", "EN→VI", "EN→EN"]


def main():
    config = load_config("device_app/config.yaml")

    display = create_display(config)
    buttons = create_buttons(config)
    power = create_power(config)
    audio = create_audio(config)

    pipeline = TranslatorPipeline(config, display, buttons, audio, power)

    current_index = 0
    current_mode = MODES[current_index]

    # Hiển thị trạng thái ban đầu
    display.clear()
    display.show_status(
        f"Mode: {current_mode}", "Ready", battery=power.get_battery_percent()
    )

    while True:
        # 1) Kiểm tra nút MODE / SHUTDOWN
        event = buttons.check_mode_or_shutdown()
        if event.toggle_mode:
            current_index = (current_index + 1) % len(MODES)
            current_mode = MODES[current_index]
            display.show_status(
                f"Mode: {current_mode}",
                "Ready",
                battery=power.get_battery_percent(),
            )

        if event.shutdown:
            display.show_status(
                "Shutting down...",
                "",
                battery=power.get_battery_percent(),
            )
            power.request_shutdown()
            break

        # 2) Chạy 1 lượt phiên dịch theo mode hiện tại
        pipeline.run_once(current_mode)


if __name__ == "__main__":
    main()
