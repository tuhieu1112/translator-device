# device_app/core/pipeline.py

from device_app.hardware.buttons import BaseButtons
from device_app.hardware.display import BaseDisplay
from device_app.hardware.audio import BaseAudio
from device_app.hardware.power import BasePower

from device_app.models.stt_vi import STTVi
from device_app.models.stt_en import STTEn
from device_app.models.nmt_vi_en import NMTViEn
from device_app.models.nmt_en_vi import NMTEnVi
from device_app.models.tts_en import TTSEn
from device_app.models.tts_vi import TTSVi


class TranslatorPipeline:
    """
    Chịu trách nhiệm:
    - Chờ nhấn TALK
    - Ghi âm (audio)
    - STT -> NMT -> TTS
    - Hiển thị trạng thái trên OLED
    """

    def __init__(self, config, display: BaseDisplay,
                 buttons: BaseButtons, audio: BaseAudio,
                 power: BasePower):
        self.config = config
        self.display = display
        self.buttons = buttons
        self.audio = audio
        self.power = power

        # Khởi tạo các model stub
        self.stt_vi = STTVi(config)
        self.stt_en = STTEn(config)
        self.nmt_vi_en = NMTViEn(config)
        self.nmt_en_vi = NMTEnVi(config)
        self.tts_en = TTSEn(config)
        self.tts_vi = TTSVi(config)

    def run_once(self, mode: str):
        """Chạy 1 lượt phiên dịch theo mode hiện tại."""

        battery = self.power.get_battery_percent()
        self.display.show_status(f"Mode: {mode}", "Ready", battery=battery)

        # 1) Chờ người dùng giữ & nhả nút TALK
        self.buttons.wait_talk_cycle()
        self.display.show_status(f"Mode: {mode}", "Recording...", battery=battery)

        # 2) Ghi âm (debug chỉ in ra, trả về tên file ảo)
        wav_in = self.audio.record_once(mode)
        self.display.show_status(f"Mode: {mode}", "Transcribing...", battery=battery)

        # 3) STT + NMT + TTS theo hướng dịch
        if mode == "VI→EN":
            text_vi = self.stt_vi.transcribe(str(wav_in))
            text_en = self.nmt_vi_en.translate(text_vi)
            self.display.show_status("VI: " + text_vi[:12],
                                     "EN: " + text_en[:12],
                                     battery=battery)
            wav_out = self.tts_en.synthesize(text_en)
        else:  # EN→VI
            text_en = self.stt_en.transcribe(str(wav_in))
            text_vi = self.nmt_en_vi.translate(text_en)
            self.display.show_status("EN: " + text_en[:12],
                                     "VI: " + text_vi[:12],
                                     battery=battery)
            wav_out = self.tts_vi.synthesize(text_vi)

        # 4) Phát âm thanh (debug chỉ in ra)
        self.display.show_status(f"Mode: {mode}", "Playing...", battery=battery)
        self.audio.play(wav_out)

        # 5) Kết thúc lượt, quay lại trạng thái sẵn sàng
        self.display.show_status(f"Mode: {mode}", "Ready", battery=battery)
