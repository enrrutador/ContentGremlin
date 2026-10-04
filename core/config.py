"""
ContentGremlin - Configuration system
Central configuration loaded from environment + user profile.
Production profile drives visual style, editing pace, B-roll, music and QA bar.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
import json
from datetime import datetime, timezone

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
CREDENTIALS_DIR = BASE_DIR / "credentials"
PROFILE_FILE = DATA_DIR / "user_profile.json"

VALID_VISUAL = frozenset({"faceless_stock", "faceless_ai", "avatar", "hybrid", "still"})
VALID_PACE = frozenset({"slow", "medium", "fast", "dynamic"})
VALID_SUBS = frozenset({"none", "minimal", "bold_faceless", "karaoke"})
VALID_QUALITY = frozenset({"draft", "review", "publishable"})
VALID_BROLL_SOURCE = frozenset({"pexels", "pixabay", "mixed"})
VALID_MUSIC_MOOD = frozenset({"auto", "upbeat", "calm", "dark", "corporate", "cinematic", "none"})


def _default_production() -> dict[str, Any]:
    return {
        "visual_style": "faceless_stock",
        "editing_pace": "medium",
        "subtitle_style": "bold_faceless",
        "quality_bar": "publishable",
        "hook_max_seconds": 3.0,
        "max_silence_seconds": 1.2,
        "min_duration_seconds": 45.0,
        "max_duration_seconds": 1200.0,
        "target_resolution": "1920x1080",
        "fps": 30,
        "transition": "crossfade",
        "transition_duration": 0.35,
        "music": {
            "enabled": True,
            "intensity": 0.22,
            "mood": "auto",
            "duck_strength": 0.65,
            "intro_fade_seconds": 1.5,
            "outro_fade_seconds": 2.0,
        },
        "broll": {
            "enabled": True,
            "source": "mixed",
            "clips_per_minute": 5,
            "min_clip_seconds": 2.5,
            "max_clip_seconds": 8.0,
            "prefer_vertical": False,
            "prefer_hd": True,
            "allow_images_fallback": True,
            "cache_days": 14,
        },
        "avatar": {
            "enabled": False,
            "provider": "none",
            "position": "pip_br",
            "scale": 0.28,
        },
        "thumbnail_style": "high_ctr",
        "brand": {
            "watermark": False,
            "watermark_text": "",
            "accent_color": "0x22c55e",
        },
    }


def _default_profile() -> dict[str, Any]:
    return {
        "mode": "supervised",
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
        "production": _default_production(),
        "created_at": None,
        "updated_at": None,
    }


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    host: str = "127.0.0.1"
    port: int = 8000
    debug: bool = True
    default_mode: Literal["supervised", "autonomous"] = "supervised"

    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o"

    anthropic_api_key: Optional[str] = None
    anthropic_model: str = "claude-3-5-sonnet-20241022"

    xai_api_key: Optional[str] = None
    xai_model: str = "grok-2"

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1"

    openrouter_api_key: Optional[str] = None
    openrouter_model: str = "qwen/qwen3.8-27b:free"

    youtube_client_secrets_file: str = "credentials/client_secrets.json"
    youtube_token_file: str = "credentials/token.json"

    elevenlabs_api_key: Optional[str] = None
    openai_tts_voice: str = "alloy"

    image_provider: str = "openai"
    openai_image_model: str = "dall-e-3"
    video_provider: str = "none"
    video_api_url: Optional[str] = None
    video_api_key: Optional[str] = None
    cinematic_max_scenes: int = 12
    cinematic_default_style: str = (
        "cinematic, shallow depth of field, natural light, 35mm film still"
    )

    # Stock B-roll
    pexels_api_key: Optional[str] = None
    pixabay_api_key: Optional[str] = None

    # Local music library (optional directory of royalty-free mp3/wav)
    music_library_dir: str = "data/music"


settings = Settings()


def normalize_production(prod: dict | None) -> dict[str, Any]:
    """Deep-merge user production config with safe defaults and clamp enums."""
    base = _default_production()
    if not isinstance(prod, dict):
        return base

    out = {**base, **{k: v for k, v in prod.items() if k not in ("music", "broll", "avatar", "brand")}}

    out["visual_style"] = out["visual_style"] if out.get("visual_style") in VALID_VISUAL else base["visual_style"]
    out["editing_pace"] = out["editing_pace"] if out.get("editing_pace") in VALID_PACE else base["editing_pace"]
    out["subtitle_style"] = (
        out["subtitle_style"] if out.get("subtitle_style") in VALID_SUBS else base["subtitle_style"]
    )
    out["quality_bar"] = out["quality_bar"] if out.get("quality_bar") in VALID_QUALITY else base["quality_bar"]

    for key in ("hook_max_seconds", "max_silence_seconds", "min_duration_seconds", "max_duration_seconds"):
        try:
            out[key] = float(out.get(key, base[key]))
        except (TypeError, ValueError):
            out[key] = base[key]

    out["transition_duration"] = max(0.0, min(1.5, float(out.get("transition_duration", 0.35))))
    out["fps"] = int(out.get("fps") or 30)

    music = {**base["music"], **(prod.get("music") or {})}
    music["intensity"] = max(0.0, min(1.0, float(music.get("intensity", 0.22))))
    music["duck_strength"] = max(0.0, min(1.0, float(music.get("duck_strength", 0.65))))
    music["mood"] = music["mood"] if music.get("mood") in VALID_MUSIC_MOOD else "auto"
    music["enabled"] = bool(music.get("enabled", True))
    out["music"] = music

    broll = {**base["broll"], **(prod.get("broll") or {})}
    broll["source"] = broll["source"] if broll.get("source") in VALID_BROLL_SOURCE else "mixed"
    broll["clips_per_minute"] = max(1, min(12, int(broll.get("clips_per_minute", 5))))
    broll["enabled"] = bool(broll.get("enabled", True))
    out["broll"] = broll

    avatar = {**base["avatar"], **(prod.get("avatar") or {})}
    avatar["enabled"] = bool(avatar.get("enabled", False))
    avatar["scale"] = max(0.1, min(0.6, float(avatar.get("scale", 0.28))))
    out["avatar"] = avatar

    brand = {**base["brand"], **(prod.get("brand") or {})}
    out["brand"] = brand

    return out


def load_user_profile() -> dict:
    """Load user profile from disk or return defaults. Migrates missing production keys."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if PROFILE_FILE.exists():
        try:
            with open(PROFILE_FILE, "r", encoding="utf-8") as f:
                profile = json.load(f)
            if not isinstance(profile, dict):
                profile = _default_profile()
            # migrate
            if "production" not in profile or not isinstance(profile.get("production"), dict):
                profile["production"] = _default_production()
            else:
                profile["production"] = normalize_production(profile["production"])
            return profile
        except Exception:
            pass

    default_profile = _default_profile()
    default_profile["mode"] = settings.default_mode
    save_user_profile(default_profile)
    return default_profile


def save_user_profile(profile: dict) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    profile = dict(profile)
    profile["updated_at"] = datetime.now(timezone.utc).isoformat()
    if not profile.get("created_at"):
        profile["created_at"] = profile["updated_at"]
    if "production" in profile:
        profile["production"] = normalize_production(profile.get("production"))
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


def get_production_config() -> dict[str, Any]:
    profile = load_user_profile()
    return normalize_production(profile.get("production"))


def update_production_config(partial: dict[str, Any]) -> dict[str, Any]:
    """Merge partial production updates into the user profile."""
    profile = load_user_profile()
    current = normalize_production(profile.get("production"))
    # shallow+nested merge for known nested keys
    merged = {**current, **{k: v for k, v in partial.items() if k not in ("music", "broll", "avatar", "brand")}}
    for nest in ("music", "broll", "avatar", "brand"):
        if nest in partial and isinstance(partial[nest], dict):
            merged[nest] = {**current.get(nest, {}), **partial[nest]}
    profile["production"] = normalize_production(merged)
    save_user_profile(profile)
    return profile["production"]
