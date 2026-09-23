"""Optional short-clip video generation. Default none → Ken Burns on stills."""
from __future__ import annotations
from pathlib import Path
from typing import Optional
import httpx
from core.config import settings, DATA_DIR

CLIP_DIR = DATA_DIR / "cinematic" / "clips"
CLIP_DIR.mkdir(parents=True, exist_ok=True)

class VideoGenProvider:
    def __init__(self):
        self.provider = (settings.video_provider or "none").lower()

    def is_configured(self) -> bool:
        if self.provider == "generic_http":
            return bool(settings.video_api_url)
        return False

    async def generate_clip(self, prompt: str, duration: float, filename: str) -> Optional[Path]:
        if not self.is_configured():
            return None
        safe = "".join(c for c in filename if c.isalnum() or c in "-_")[:40] or "clip"
        out = CLIP_DIR / f"{safe}.mp4"
        headers = {"Content-Type": "application/json"}
        if settings.video_api_key:
            headers["Authorization"] = f"Bearer {settings.video_api_key}"
        async with httpx.AsyncClient(timeout=300) as client:
            r = await client.post(settings.video_api_url, headers=headers, json={"prompt": prompt, "duration": duration})
            if r.status_code >= 400:
                raise RuntimeError(f"Video API error: {r.status_code} {r.text[:400]}")
            data = r.json()
            url = data.get("video_url") or data.get("url")
            if not url:
                raise RuntimeError("Video API missing video_url")
            vid = await client.get(url)
            vid.raise_for_status()
            out.write_bytes(vid.content)
        return out
