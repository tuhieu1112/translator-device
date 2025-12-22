import re
import unicodedata
from typing import Dict, Tuple


class SkeletonTranslator:
    """
    Skeleton Translation – FINAL SAFE VERSION (VI + EN)

    MỤC TIÊU:
    - Ngăn OPUS dịch sai tên riêng (lake / president / nonsense)
    - KHÔNG phá cấu trúc câu
    - KHÔNG map tên
    - KHÔNG NER
    - Hoạt động ổn định với câu dài, STT thực tế

    NGUYÊN TẮC:
    - VI: CHỈ cắt tên riêng SAU TỪ CHỈ LOẠI (đường, quận, thành phố...)
    - EN: cắt chuỗi Capitalized (EN STT ổn hơn)
    - Giới hạn độ dài + biên dừng an toàn
    """

    # =====================================================
    # VI: Proper noun sau từ chỉ loại (SAFE HEURISTIC)
    # =====================================================
    # Ví dụ match:
    #   "đường hoàng hoa thám"
    #   "quận bến thành"
    #   "thành phố hồ chí minh"
    #
    # KHÔNG match sang mệnh đề sau
    VI_TYPED = re.compile(
        r"\b(đường|phố|quận|huyện|thành phố|tỉnh)\s+"
        r"([a-zà-ỹ]+(?:\s+[a-zà-ỹ]+){0,2})"
        r"(?=\s+(vì|để|là|mà|với|do|khi|trong|ngoài|ở|tại)\b|$)",
        flags=re.IGNORECASE,
    )

    # =====================================================
    # EN: Capitalized proper nouns (EN STT khá ổn định)
    # =====================================================
    # Ví dụ:
    #   "Ho Chi Minh City"
    #   "Ben Thanh"
    #   "Nguyen Trai"
    EN_PROPER = re.compile(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})\b")

    # ===================== HELPERS =======================

    @staticmethod
    def latinize(text: str) -> str:
        """
        Bỏ dấu tiếng Việt – KHÔNG map
        """
        return (
            unicodedata.normalize("NFD", text).encode("ascii", "ignore").decode("utf-8")
        )

    # ===================== VI → EN =======================

    def extract_vi(self, text: str) -> Tuple[str, Dict[str, str]]:
        """
        Tách skeleton cho tiếng Việt

        Return:
          - skeleton_text (còn ngữ pháp)
          - slots: { "[PN0]": "Hoang Hoa Tham", ... }
        """
        slots: Dict[str, str] = {}
        idx = 0

        def _typed(m):
            nonlocal idx
            slot = f"[PN{idx}]"
            # chỉ latinize phần tên, GIỮ từ chỉ loại
            slots[slot] = self.latinize(m.group(2))
            idx += 1
            return f"{m.group(1)} {slot}"

        skeleton = self.VI_TYPED.sub(_typed, text)
        skeleton = " ".join(skeleton.split())

        return skeleton, slots

    # ===================== EN → VI =======================

    def extract_en(self, text: str) -> Tuple[str, Dict[str, str]]:
        """
        Tách skeleton cho tiếng Anh
        """
        slots: Dict[str, str] = {}
        idx = 0

        def _plain(m):
            nonlocal idx
            slot = f"[PN{idx}]"
            slots[slot] = m.group(1)
            idx += 1
            return slot

        skeleton = self.EN_PROPER.sub(_plain, text)
        skeleton = " ".join(skeleton.split())

        return skeleton, slots

    # ===================== COMPOSE =======================

    def compose(self, translated: str, slots: Dict[str, str]) -> str:
        """
        Ghép lại proper nouns đúng vị trí slot
        """
        for slot, value in slots.items():
            translated = translated.replace(slot, value)
        return translated
