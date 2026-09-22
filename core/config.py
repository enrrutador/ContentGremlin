"""
ContentGremlin - Configuration system
Central configuration loaded from environment + user profile.
"""

from pathlib import Path
from typing import Optional, Literal
from pydantic_settings import BaseSettings
from pydantic import Field
import json

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
CREDENTIALS_DIR = BASE_DIR / "credentials"
PROFILE_FILE = DATA_DIR / "user_profile.json"


class Settings(BaseSettings):
    # Application
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True
    default_mode: Literal["supervised", "autonomous"] = "supervised"

    # LLM Providers (at least one should be set)
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o"

    anthropic_api_key: Optional[str] = None
    anthropic_model: str = "claude-3-5-sonnet-20241022"

    xai_api_key: Optional[str] = None
    xai_model: str = "grok-2"

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1"

    openrouter_api_key: Optional[str] = None

    # YouTube (optional)
    youtube_client_secrets_file: str = "credentials/client_secrets.json"
    youtube_token_file: str = "credentials/token.json"

    # TTS
    elevenlabs_api_key: Optional[str] = None
    openai_tts_voice: str = "alloy"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()


def load_user_profile() -> dict:
    """Load user profile from disk or return defaults."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if PROFILE_FILE.exists():
        try:
            with open(PROFILE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass

    default_profile = {
        "mode": settings.default_mode,
        "niche": "",
        "style_preferences": {
            "tone": "professional yet engaging",
            "hook_style": "strong curiosity",
            "preferred_length_minutes": 8,
            "language": "es",
        },
        "llm_provider": "openai",
        "tts_provider": "openai",
        "autonomous_upload_allowed": False,
        "created_at": None,
        "updated_at": None,
    }
    save_user_profile(default_profile)
    return default_profile


def save_user_profile(profile: dict) -> None:
    """Save user profile to disk."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(PROFILE_FILE, "w", encoding="utf-8") as f:
        json.dump(profile, f, indent=2, ensure_ascii=False)


def get_active_mode() -> str:
    profile = load_user_profile()
    return profile.get("mode", settings.default_mode)


def set_mode(mode: Literal["supervised", "autonomous"]) -> dict:
    profile = load_user_profile()
    profile["mode"] = mode
    save_user_profile(profile)
    return profile
