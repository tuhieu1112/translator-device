from device_app.utils.config import load_config
from device_app.hardware.display import create_display
from device_app.hardware.buttons import create_buttons
from device_app.hardware.power import create_power
from device_app.hardware.audio import create_audio
from device_app.core.pipeline import TranslatorPipeline


def main():
    config = load_config("device_app/config.yaml")

    display = create_display(config)
    buttons = create_buttons(config)
    power = create_power(config)
    audio = create_audio(config)

    pipeline = TranslatorPipeline(config, display, buttons, audio, power)

    current_mode = "VI→EN"  # mặc định

    while True:
        # Kiểm tra đổi mode / shutdown (bản debug hiện chưa làm gì)
        event = buttons.check_mode_or_shutdown()
        if event.toggle_mode:
            current_mode = "EN→VI" if current_mode == "VI→EN" else "VI→EN"

        if event.shutdown:
            display.show_status("Shutting down...", "", battery=power.get_battery_percent())
            power.request_shutdown()
            break

        # Chạy 1 lượt phiên dịch
        pipeline.run_once(current_mode)


if __name__ == "__main__":
    main()
