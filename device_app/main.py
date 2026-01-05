from pathlib import Path

from device_app.core.modes import Mode
from device_app.core.pipeline import TranslatorPipeline

from device_app.utils.config import load_config
from device_app.hardware.display import create_display
from device_app.hardware.buttons import create_buttons
from device_app.hardware.audio import create_audio
from device_app.hardware.power import create_power_manager


def main() -> None:
    here = Path(__file__).resolve().parent
    config = load_config(here / "config.yaml")

    pipeline = TranslatorPipeline(
        config=config,
        display=create_display(config),
        buttons=create_buttons(config),
        audio=create_audio(config),
        power=create_power_manager(config),
    )

    pipeline.run(start_mode=Mode.VI_EN)


if __name__ == "__main__":
    main()
