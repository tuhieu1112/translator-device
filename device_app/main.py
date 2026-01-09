from pathlib import Path

from device_app.core.modes import Mode
from device_app.core.pipeline import TranslatorPipeline

from device_app.utils.config import load_config
from device_app.hardware.display import create_display
from device_app.hardware.buttons import create_buttons
from device_app.hardware.audio import create_audio
from device_app.hardware.power import create_power_manager

# (tuỳ giai đoạn DEV / PROD)
# from device_app.models.stt import create_stt
# from device_app.models.nmt import create_nmt
# from device_app.models.tts import create_tts


def main() -> None:
    here = Path(__file__).resolve().parent
    config = load_config(here / "config.yaml")

    # ========== HARDWARE ==========
    display = create_display(config)
    buttons = create_buttons(config)
    audio = create_audio(config)
    power = create_power_manager(config)

    # ========== MODELS ==========
    pipeline = TranslatorPipeline(
        display=display,
        buttons=buttons,
        audio=audio,
        power=power,
        device_env=config.get("DEVICE_ENV", "DEV"),
        # models – BẮT BUỘC
        stt_vi=create_stt_vi(config),
        stt_en=create_stt_en(config),
        nmt_vi_en=create_nmt_vi_en(config),
        nmt_en_vi=create_nmt_en_vi(config),
        tts_vi=create_tts_vi(config),
        tts_en=create_tts_en(config),
        nlp_vi=create_nlp_vi(config),
        nlp_en=create_nlp_en(config),
        skeleton=create_skeleton(config),
    )

    pipeline.run(start_mode=Mode.VI_EN)


if __name__ == "__main__":
    main()
