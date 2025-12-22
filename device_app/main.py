# device_app/main.py
from __future__ import annotations

# ==============================
# 🔥 ENV MUST BE SET FIRST (CRITICAL)
# ==============================
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
ARTIFACTS = BASE_DIR / "artifacts"
HF_CACHE = ARTIFACTS / "hf_cache"
TMP_DIR = ARTIFACTS / "tmp"

HF_CACHE.mkdir(parents=True, exist_ok=True)
TMP_DIR.mkdir(parents=True, exist_ok=True)

# 🔥 WINDOWS + LINUX SAFE
os.environ["HF_HOME"] = str(HF_CACHE)
os.environ["TRANSFORMERS_CACHE"] = str(HF_CACHE)

# 🔥 WINDOWS TEMP (QUAN TRỌNG)
os.environ["TEMP"] = str(TMP_DIR)
os.environ["TMP"] = str(TMP_DIR)

# ❌ KHÔNG SET TMPDIR TRÊN WINDOWS
# os.environ["TMPDIR"] = str(TMP_DIR)  # ❌ BỎ


# ==============================
# SAU KHI SET ENV → MỚI IMPORT
# ==============================
from device_app.core.modes import Mode
from device_app.core.pipeline import TranslatorPipeline
from device_app.hardware.audio import create_audio
from device_app.hardware.buttons import create_buttons
from device_app.hardware.display import create_display
from device_app.hardware.power import create_power_manager
from device_app.utils.config import load_config


# ==============================
# MODE SWITCH
# ==============================
def next_mode(current: Mode) -> Mode:
    if current is Mode.VI_EN:
        return Mode.EN_VI
    if current is Mode.EN_VI:
        return Mode.VI_EN
    return Mode.VI_EN


def main() -> None:
    here = Path(__file__).resolve().parent
    config = load_config(here / "config.yaml")

    display = create_display(config)
    buttons = create_buttons(config)
    audio = create_audio(config)
    power = create_power_manager(config)

    pipeline = TranslatorPipeline(
        config,
        display,
        buttons,
        audio,
        power,
    )

    mode = Mode.VI_EN
    display.show_mode(mode)

    print("[MAIN] Device loop started.")

    while True:
        cmd = input("\n[MAIN] Enter/m/p/q: ").strip().lower()

        if cmd == "q":
            print("[MAIN] Exit.")
            break

        if cmd == "m":
            mode = next_mode(mode)
            display.show_mode(mode)
            continue

        if cmd == "p":
            power.shutdown()
            continue

        pipeline.run_once(mode)


if __name__ == "__main__":
    main()
