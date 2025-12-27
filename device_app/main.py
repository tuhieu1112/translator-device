from __future__ import annotations

import os
from pathlib import Path

# ===== ENV =====
BASE_DIR = Path(__file__).resolve().parent.parent
ARTIFACTS = BASE_DIR / "artifacts"
HF_CACHE = ARTIFACTS / "hf_cache"
TMP_DIR = ARTIFACTS / "tmp"

HF_CACHE.mkdir(parents=True, exist_ok=True)
TMP_DIR.mkdir(parents=True, exist_ok=True)

os.environ["HF_HOME"] = str(HF_CACHE)
os.environ["TRANSFORMERS_CACHE"] = str(HF_CACHE)
os.environ["TEMP"] = str(TMP_DIR)
os.environ["TMP"] = str(TMP_DIR)

# ===== IMPORT =====
from device_app.core.modes import Mode
from device_app.core.pipeline import TranslatorPipeline
from device_app.hardware.audio import create_audio
from device_app.hardware.buttons import create_buttons
from device_app.hardware.display import create_display
from device_app.hardware.power import create_power_manager
from device_app.utils.config import load_config


def main() -> None:
    here = Path(__file__).resolve().parent
    config = load_config(here / "config.yaml")

    display = create_display(config)
    buttons = create_buttons(config)
    audio = create_audio(config)
    power = create_power_manager(config)

    pipeline = TranslatorPipeline(
        config=config,
        display=display,
        buttons=buttons,
        audio=audio,
        power=power,
    )

    mode = Mode.VI_EN
    display.show_mode(mode)

    print("[MAIN] Device loop started")

    while True:
        buttons.wait_talk()
        pipeline.run_once(mode)


if __name__ == "__main__":
    main()
