# device_app/core/state.py
from enum import Enum, auto


class State(Enum):
    """
    Trạng thái hoạt động của thiết bị (FSM)
    """

    READY = auto()
    RECORDING = auto()
    TRANSLATING = auto()
    SPEAKING = auto()
