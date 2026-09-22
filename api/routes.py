"""
ContentGremlin - API Routes
Clean endpoints designed for both the web UI and external agents.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Literal, Any
from core.mode_manager import ModeManager
from core.config import load_user_profile, save_user_profile, settings
from core.safety import safety_report, can_upload
from modules.analyzer import analyze_channel

router = APIRouter()


class ModeRequest(BaseModel):
    mode: Literal["supervised", "autonomous"]


class AnalyzeRequest(BaseModel):
    channel_url: str = Field(..., description="YouTube channel URL or handle")


class ProfileUpdate(BaseModel):
    niche: Optional[str] = None
    tone: Optional[str] = None
    language: Optional[str] = None
    llm_provider: Optional[str] = None
    autonomous_upload_allowed: Optional[bool] = None


@router.get("/status")
async def get_status():
    profile = load_user_profile()
    return {
        "status": "online",
        "mode": ModeManager.current(),
        "niche": profile.get("niche", ""),
        "llm_provider": profile.get("llm_provider", "not set"),
        "youtube_configured": False,
        "safety": safety_report(),
        "version": "0.1.0",
    }


@router.post("/set_mode")
async def set_mode(req: ModeRequest):
    profile = ModeManager.set(req.mode)
    return {
        "success": True,
        "mode": profile["mode"],
        "message": f"Mode changed to {profile['mode']}",
    }


@router.get("/mode")
async def get_mode():
    return {"mode": ModeManager.current()}


@router.get("/profile")
async def get_profile():
    return load_user_profile()


@router.post("/profile")
async def update_profile(update: ProfileUpdate):
    profile = load_user_profile()
    if update.niche is not None:
        profile["niche"] = update.niche
    if update.tone is not None:
        profile.setdefault("style_preferences", {})["tone"] = update.tone
    if update.language is not None:
        profile.setdefault("style_preferences", {})["language"] = update.language
    if update.llm_provider is not None:
        profile["llm_provider"] = update.llm_provider
    if update.autonomous_upload_allowed is not None:
        profile["autonomous_upload_allowed"] = update.autonomous_upload_allowed
    save_user_profile(profile)
    return {"success": True, "profile": profile}


@router.get("/config/public")
async def get_public_config():
    return {
        "host": settings.host,
        "port": settings.port,
        "debug": settings.debug,
        "default_mode": settings.default_mode,
        "openai_configured": bool(settings.openai_api_key),
        "anthropic_configured": bool(settings.anthropic_api_key),
        "xai_configured": bool(settings.xai_api_key),
        "ollama_base_url": settings.ollama_base_url,
        "elevenlabs_configured": bool(settings.elevenlabs_api_key),
    }


@router.post("/analyze_channel")
async def api_analyze_channel(req: AnalyzeRequest):
    try:
        report = analyze_channel(req.channel_url)
        return {
            "success": True,
            "report": report,
            "requires_approval": ModeManager.requires_approval("analysis"),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/generate_ideas")
async def generate_ideas_placeholder(payload: dict[str, Any] = None):
    return {
        "success": True,
        "message": "Idea generation module is under construction. Analyzer is ready.",
        "ideas": [],
        "requires_approval": ModeManager.requires_approval("ideas"),
    }


@router.get("/safety")
async def get_safety():
    return safety_report()
