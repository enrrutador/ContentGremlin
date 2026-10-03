"""
ContentGremlin - Production API routes
Publish-ready pipeline: profile, produce, QA, broll/music status.
"""
from __future__ import annotations

from typing import Any, Optional
import asyncio
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core.config import get_production_config, update_production_config
from core.jobs import submit_job
from core.mode_manager import ModeManager
from modules.library import add_item

router = APIRouter()


class ProductionUpdate(BaseModel):
    visual_style: Optional[str] = None
    editing_pace: Optional[str] = None
    subtitle_style: Optional[str] = None
    quality_bar: Optional[str] = None
    music: Optional[dict[str, Any]] = None
    broll: Optional[dict[str, Any]] = None
    avatar: Optional[dict[str, Any]] = None
    brand: Optional[dict[str, Any]] = None
    hook_max_seconds: Optional[float] = None
    max_silence_seconds: Optional[float] = None
    min_duration_seconds: Optional[float] = None
    max_duration_seconds: Optional[float] = None
    target_resolution: Optional[str] = None
    transition: Optional[str] = None
    transition_duration: Optional[float] = None
    fps: Optional[int] = None


class ProduceRequest(BaseModel):
    script: str
    title: str
    voice: Optional[str] = None
    idea: Optional[dict[str, Any]] = None
    skip_qa: bool = False


class QARequest(BaseModel):
    video_path: str
    audio_path: Optional[str] = None
    script: Optional[str] = None


@router.get("/production")
async def api_get_production():
    return {"production": get_production_config()}


@router.post("/production")
async def api_update_production(update: ProductionUpdate):
    partial = update.model_dump(exclude_none=True)
    prod = update_production_config(partial)
    return {"success": True, "production": prod}


@router.post("/produce")
async def api_produce(req: ProduceRequest):
    try:
        from modules.production_engine import produce

        result = await produce(
            script=req.script,
            title=req.title,
            voice=req.voice,
            idea=req.idea,
            skip_qa=req.skip_qa,
        )
        entry = add_item(
            item_type="production",
            title=req.title,
            content=result,
            meta={
                "publishable": result.get("publishable"),
                "visual_style": result.get("visual_style"),
                "qa_score": (result.get("qa") or {}).get("score"),
            },
        )
        result["library_id"] = entry["id"]
        result["requires_approval"] = ModeManager.requires_approval("video")
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/produce_async")
async def api_produce_async(req: ProduceRequest):
    from modules.production_engine import produce

    def _runner():
        return asyncio.run(
            produce(
                script=req.script,
                title=req.title,
                voice=req.voice,
                idea=req.idea,
                skip_qa=req.skip_qa,
            )
        )

    job = submit_job("produce", _runner)
    return {
        "success": True,
        "job_id": job["id"],
        "status": job["status"],
        "poll": f"/api/jobs/{job['id']}",
    }


@router.post("/qa")
async def api_qa(req: QARequest):
    try:
        from modules.qa_agent import run_qa
        from core.storage import has_allowed_ext, VIDEO_EXTS

        if not has_allowed_ext(req.video_path, VIDEO_EXTS):
            raise HTTPException(status_code=400, detail="video_path must be a video file")
        result = run_qa(req.video_path, audio_path=req.audio_path, script=req.script)
        return {"success": True, **result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/broll/status")
async def api_broll_status():
    from modules.broll import broll_status

    return broll_status()


@router.get("/music/status")
async def api_music_status():
    from modules.audio_mix import music_library_status

    return music_library_status()
