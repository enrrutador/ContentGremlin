"""Image generation for cinematic mode."""
from __future__ import annotations
from pathlib import Path
import httpx
from core.config import settings, DATA_DIR

IMAGE_DIR = DATA_DIR / "cinematic" / "images"
IMAGE_DIR.mkdir(parents=True, exist_ok=True)

class ImageProvider:
    def __init__(self):
        self.provider = (settings.image_provider or "openai").lower()

    def is_configured(self) -> bool:
        if self.provider == "none":
            return False
        return bool(settings.openai_api_key)

    async def generate(self, prompt: str, filename: str, size: str = "1792x1024") -> Path:
        if not self.is_configured():
            raise RuntimeError("Image provider not configured. Set OPENAI_API_KEY and IMAGE_PROVIDER=openai.")
        safe = "".join(c for c in filename if c.isalnum() or c in "-_")[:40] or "scene"
        out = IMAGE_DIR / f"{safe}.png"
        return await self._openai(prompt, out, size)

    async def _openai(self, prompt: str, out: Path, size: str) -> Path:
        if size not in ("1024x1024", "1792x1024", "1024x1792"):
            size = "1792x1024"
        headers = {"Authorization": f"Bearer {settings.openai_api_key}", "Content-Type": "application/json"}
        body = {"model": settings.openai_image_model or "dall-e-3", "prompt": prompt[:4000], "n": 1, "size": size, "response_format": "url"}
        async with httpx.AsyncClient(timeout=120) as client:
            r = await client.post("https://api.openai.com/v1/images/generations", headers=headers, json=body)
            if r.status_code >= 400:
                raise RuntimeError(f"OpenAI image error: {r.status_code} {r.text[:400]}")
            url = r.json()["data"][0]["url"]
            img = await client.get(url)
            img.raise_for_status()
            out.write_bytes(img.content)
        return out
