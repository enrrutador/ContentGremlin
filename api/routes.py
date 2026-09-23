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
from modules.idea_generator import generate_ideas
from modules.script_writer import write_script
from modules.library import add_item, list_items, get_item, delete_item
from modules.video_creator import create_video_from_script_and_audio
from providers.tts import TTSProvider
from pathlib import Path

router = APIRouter()


# ---------- Models ----------

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


class GenerateIdeasRequest(BaseModel):
    analysis_report: dict[str, Any]
    count: int = 8
    niche: Optional[str] = None


class WriteScriptRequest(BaseModel):
    idea: dict[str, Any]
    language: Optional[str] = None


# ---------- Status & Mode ----------

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


# ---------- Profile & Config ----------

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
    """Safe config values that can be shown in the UI."""
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


# ---------- Core Pipeline ----------

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
async def api_generate_ideas(req: GenerateIdeasRequest):
    try:
        ideas = await generate_ideas(
            analysis_report=req.analysis_report,
            count=req.count,
            niche=req.niche,
        )
        for idea in ideas:
            add_item(
                item_type="idea",
                title=idea.get("title", "Idea"),
                content=idea,
            )
        return {
            "success": True,
            "ideas": ideas,
            "count": len(ideas),
            "requires_approval": ModeManager.requires_approval("ideas"),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/write_script")
async def api_write_script(req: WriteScriptRequest):
    try:
        script = await write_script(idea=req.idea, language=req.language)
        entry = add_item(
            item_type="script",
            title=req.idea.get("title", "Script"),
            content=script,
            meta={"idea": req.idea},
        )
        return {
            "success": True,
            "script": script,
            "library_id": entry["id"],
            "requires_approval": ModeManager.requires_approval("script"),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/safety")
async def get_safety():
    return safety_report()


# ---------- Voice / Video / Library ----------

class VoiceRequest(BaseModel):
    text: str
    title: Optional[str] = "narration"
    voice: Optional[str] = None


class VideoRequest(BaseModel):
    audio_path: str
    title: str
    output_name: Optional[str] = None


class FullPipelineRequest(BaseModel):
    """Generate voice + simple video from a script in one call."""
    script: str
    title: str
    voice: Optional[str] = None


@router.post("/generate_voice")
async def api_generate_voice(req: VoiceRequest):
    try:
        tts = TTSProvider()
        path = await tts.generate(text=req.text, filename=req.title, voice=req.voice)
        entry = add_item(
            item_type="audio",
            title=req.title,
            content=str(path),
            meta={"chars": len(req.text)},
        )
        return {
            "success": True,
            "audio_path": str(path),
            "library_id": entry["id"],
            "requires_approval": ModeManager.requires_approval("voice"),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/create_video")
async def api_create_video(req: VideoRequest):
    try:
        result = create_video_from_script_and_audio(
            script="",
            audio_path=Path(req.audio_path),
            title=req.title,
            output_name=req.output_name,
        )
        entry = add_item(
            item_type="video",
            title=req.title,
            content=result["video_path"],
            meta=result,
        )
        return {
            "success": True,
            **result,
            "library_id": entry["id"],
            "requires_approval": ModeManager.requires_approval("video"),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/full_pipeline")
async def api_full_pipeline(req: FullPipelineRequest):
    """Convenience: script → voice → simple video."""
    try:
        tts = TTSProvider()
        audio_path = await tts.generate(text=req.script, filename=req.title, voice=req.voice)
        result = create_video_from_script_and_audio(
            script=req.script,
            audio_path=audio_path,
            title=req.title,
            output_name=req.title,
        )
        entry = add_item(
            item_type="full_project",
            title=req.title,
            content={
                "script": req.script,
                "audio_path": str(audio_path),
                "video_path": result["video_path"],
            },
            meta=result,
        )
        return {
            "success": True,
            "audio_path": str(audio_path),
            "video_path": result["video_path"],
            "library_id": entry["id"],
            "requires_approval": ModeManager.requires_approval("video"),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/library")
async def api_list_library(type: Optional[str] = None, limit: int = 50):
    return {"items": list_items(item_type=type, limit=limit)}


@router.get("/library/{item_id}")
async def api_get_library_item(item_id: str):
    item = get_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@router.delete("/library/{item_id}")
async def api_delete_library_item(item_id: str):
    ok = delete_item(item_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"success": True}
