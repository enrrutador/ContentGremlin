"""Bridge ContentGremlin → video_editor (localhost:3000)."""
from __future__ import annotations
from typing import Any, Optional
import httpx

DEFAULT_EDITOR = "http://127.0.0.1:3000"


async def editor_health(base_url: str = DEFAULT_EDITOR) -> dict[str, Any]:
    try:
        async with httpx.AsyncClient(timeout=3) as client:
            r = await client.get(f"{base_url}/api/capabilities")
            if r.status_code == 200:
                return {"ok": True, **r.json()}
            r = await client.get(f"{base_url}/")
            return {"ok": r.status_code < 500, "status": r.status_code}
    except Exception as e:
        return {"ok": False, "error": str(e)}


async def send_to_editor(
    video_path: Optional[str] = None,
    media_paths: Optional[list[str]] = None,
    name: str = "From Gremlin",
    auto_assemble: bool = True,
    crossfade: float = 0,
    base_url: str = DEFAULT_EDITOR,
) -> dict[str, Any]:
    paths = list(media_paths or [])
    if video_path and video_path not in paths:
        paths.insert(0, video_path)
    body = {
        "name": name,
        "videoPath": video_path,
        "mediaPaths": paths,
        "autoAssemble": auto_assemble,
        "crossfade": crossfade,
    }
    async with httpx.AsyncClient(timeout=120) as client:
        r = await client.post(f"{base_url}/api/integrate/gremlin", json=body)
        r.raise_for_status()
        return r.json()
