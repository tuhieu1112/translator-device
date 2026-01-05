"""
Test IMPORT & BOOTSTRAP level
- Không load model
- Không đụng phần cứng
- Dùng cho Windows / VSCode
"""

import sys
from pathlib import Path
import os

# --------------------------------------------------
# Add project root to PYTHONPATH
# --------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# --------------------------------------------------
# DEV MODE
# --------------------------------------------------
os.environ["DEVICE_ENV"] = "DEV"

print("[TEST] DEVICE_ENV =", os.getenv("DEVICE_ENV"))

print("[TEST] Importing TranslatorPipeline...")

from device_app.core.pipeline import TranslatorPipeline
from device_app.core.modes import Mode

print("[TEST] Import OK")


# --------------------------------------------------
# Dummy hardware
# --------------------------------------------------
class Dummy:
    def __getattr__(self, name):
        return lambda *args, **kwargs: None


# --------------------------------------------------
# Init pipeline
# --------------------------------------------------
pipeline = TranslatorPipeline(
    config={},
    display=Dummy(),
    buttons=Dummy(),
    audio=Dummy(),
    power=Dummy(),
)

print("[TEST] Pipeline initialized successfully")

pipeline.display.show_mode(Mode.VI_EN)
pipeline.display.show_battery(80)

print("\n[TEST RESULT] ✅ PROJECT IMPORT & INIT PASSED")
