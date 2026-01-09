from pathlib import Path

from device_app.core.modes import Mode
from device_app.core.pipeline import TranslatorPipeline

from device_app.utils.config import load_config

# ========== HARDWARE ==========
from device_app.hardware.display import create_display
from device_app.hardware.buttons import create_buttons
from device_app.hardware.audio import create_audio
from device_app.hardware.power import create_power_manager

# ========== MODELS ==========
from device_app.models.stt_vi import SttVi
from device_app.models.stt_en import SttEn

from device_app.models.nmt_vi_en import NmtViEn
from device_app.models.nmt_en_vi import NmtEnVi

from device_app.models.tts_vi import TtsVi
from device_app.models.tts_en import TtsEn

from device_app.models.nlp_vi import NlpVi
from device_app.models.nlp_en import NlpEn

from device_app.models.skeleton_translation import SkeletonTranslation


def main() -> None:
    here = Path(__file__).resolve().parent
    config = load_config(here / "config.yaml")

    # ========== HARDWARE ==========
    display = create_display(config)
    buttons = create_buttons(config)
    audio = create_audio(config)
    power = create_power_manager(config)

    # ========== MODELS ==========
    stt_vi = SttVi(config)
    stt_en = SttEn(config)

    nmt_vi_en = NmtViEn(config)
    nmt_en_vi = NmtEnVi(config)

    tts_vi = TtsVi(config)
    tts_en = TtsEn(config)

    nlp_vi = NlpVi(config)
    nlp_en = NlpEn(config)

    skeleton = SkeletonTranslation(config)

    # ========== PIPELINE ==========
    pipeline = TranslatorPipeline(
        display=display,
        buttons=buttons,
        audio=audio,
        power=power,
        device_env=config.get("DEVICE_ENV", "REAL"),
        # models – BẮT BUỘC
        stt_vi=stt_vi,
        stt_en=stt_en,
        nmt_vi_en=nmt_vi_en,
        nmt_en_vi=nmt_en_vi,
        tts_vi=tts_vi,
        tts_en=tts_en,
        nlp_vi=nlp_vi,
        nlp_en=nlp_en,
        skeleton=skeleton,
    )

    pipeline.run(start_mode=Mode.VI_EN)


if __name__ == "__main__":
    main()
