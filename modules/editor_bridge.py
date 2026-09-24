"""Bridge ContentGremlin → video_editor (localhost:3000)."""
from __future__ import annotations
from typing import Any, Optional
import httpx

DEFAULT_EDITOR = "http://127.0.0.1:3000"

async def send_to_editor(
    video_path: Optional[str] = None,
    media_paths: Optional[list[str]] = None,
    name: str = "From Gremlin",
    auto_assemble: bool = True,
    crossfade: float = 0,
    base_url: str = DEFAULT_EDITOR,
) -> dict[str, Any]:
    body = {
        "name": name,
        "videoPath": video_path,
        "mediaPaths": media_paths or [],
        "autoAssemble": auto_assemble,
        "crossfade": crossfade,
    }
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(f"{base_url}/api/integrate/gremlin", json=body)
        r.raise_for_status()
        return r.json()
