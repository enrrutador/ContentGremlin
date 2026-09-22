"""
ContentGremlin - Mode Manager
Handles Supervised vs Autonomous operation.
"""

from typing import Literal
from .config import get_active_mode, set_mode, load_user_profile


Mode = Literal["supervised", "autonomous"]


class ModeManager:
    @staticmethod
    def current() -> Mode:
        return get_active_mode()  # type: ignore

    @staticmethod
    def set(mode: Mode) -> dict:
        if mode not in ("supervised", "autonomous"):
            raise ValueError("Mode must be 'supervised' or 'autonomous'")
        return set_mode(mode)

    @staticmethod
    def is_autonomous() -> bool:
        return ModeManager.current() == "autonomous"

    @staticmethod
    def is_supervised() -> bool:
        return ModeManager.current() == "supervised"

    @staticmethod
    def requires_approval(step: str) -> bool:
        """
        In supervised mode almost every important step needs approval.
        In autonomous mode only critical safety steps may still require it.
        """
        if ModeManager.is_autonomous():
            return step in ("upload",) and not load_user_profile().get("autonomous_upload_allowed", False)
        return step in ("ideas", "script", "video", "metadata", "upload")
