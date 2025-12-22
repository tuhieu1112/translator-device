# device_app/models/nlp/csp.py
import re
from typing import Dict, Tuple


class CSP:
    """
    Contextual Semantic Protection
    - Không hard-code tên
    - Không danh sách địa danh
    - Nhận diện vai trò từ NGỮ CẢNH
    - Dùng token hợp MarianMT
    """

    VI_PATTERNS = [
        (r"(đường|phố)\s+(.+)", "street"),
        (r"(ở|đến|đi)\s+(.+)", "location"),
        (r"(gặp)\s+(anh|chị)?\s*(.+)", "person"),
        (r"(học|làm)\s+ở\s+(.+)", "organization"),
    ]

    EN_PATTERNS = [
        (r"(street|road|avenue)\s+(.+)", "street"),
        (r"(in|to)\s+(.+)", "location"),
        (r"(meet)\s+(mr|ms)?\.?\s*(.+)", "person"),
        (r"(study|work)\s+at\s+(.+)", "organization"),
    ]

    ROLE_TOKEN = {
        "street": "zzstreet",
        "location": "zzplace",
        "person": "zzperson",
        "organization": "zzorg",
    }

    def __init__(self, lang: str):
        self.lang = lang

    def protect(self, text: str) -> Tuple[str, Dict[str, Dict]]:
        """
        Trả về:
        - text đã thay thế token
        - entities map để restore
        """
        entities = {}
        patterns = self.VI_PATTERNS if self.lang == "vi" else self.EN_PATTERNS

        protected_text = text

        for pat, role in patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if not m:
                continue

            name = m.groups()[-1].strip()
            token = self.ROLE_TOKEN[role]

            protected_text = text.replace(name, token)
            entities[token] = {
                "value": name,
                "role": role,
            }
            break  # chỉ xử lý 1 thực thể / câu

        return protected_text, entities

    def restore(self, text: str, entities: Dict[str, Dict]) -> str:
        restored = text

        for token, info in entities.items():
            value = info["value"]
            role = info["role"]

            if self.lang == "en":
                if role == "street":
                    value = f"{value} street"
                elif role == "location":
                    value = value
                elif role == "person":
                    value = value
                elif role == "organization":
                    value = value

            restored = restored.replace(token, value)

        return restored
