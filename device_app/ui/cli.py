# device_app/ui/cli.py
from __future__ import annotations

from typing import Iterable
from device_app.core.modes import Mode


def _print_modes(modes: Iterable[Mode]) -> None:
    print("\n===== CHỌN CHẾ ĐỘ DỊCH (DEBUG CLI) =====")
    for idx, m in enumerate(modes, start=1):
        # Ví dụ VI_EN -> "VI→EN"
        if m is Mode.VI_EN:
            label = "VI → EN (nói tiếng Việt, dịch sang Anh)"
        elif m is Mode.EN_VI:
            label = "EN → VI (nói tiếng Anh, dịch sang Việt)"
        else:
            label = "EN → EN (sửa / cải thiện câu tiếng Anh)"
        print(f"  {idx}. {label}")
    print("========================================")


def ask_mode(default: Mode = Mode.EN_VI) -> Mode:
    """
    Hỏi người dùng chọn chế độ dịch khi chạy trên laptop
    (BUTTON_MODE=debug). Trên thiết bị thật, chế độ sẽ đổi bằng
    nút MODE nên không cần dùng hàm này.

    Nếu người dùng chỉ nhấn Enter thì dùng chế độ mặc định.
    """
    modes = [Mode.VI_EN, Mode.EN_VI, Mode.EN_EN]

    _print_modes(modes)
    ans = input(
        f"Nhập số (1-{len(modes)}) để chọn, hoặc Enter để dùng mặc định "
        f"[{default.name}]: "
    ).strip()

    if ans:
        try:
            idx = int(ans)
            if 1 <= idx <= len(modes):
                chosen = modes[idx - 1]
                print(f"--> Đã chọn chế độ: {chosen.name}")
                return chosen
        except ValueError:
            # nhập bậy thì rơi xuống dùng default
            pass

    print(f"--> Dùng chế độ mặc định: {default.name}")
    return default


__all__ = ["ask_mode"]
