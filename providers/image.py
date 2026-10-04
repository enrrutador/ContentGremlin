"""Image generation for cinematic mode.

Providers (IMAGE_PROVIDER):
  pollinations - gratis, sin key (default). https://pollinations.ai
  openai       - DALL-E, pago (OPENAI_API_KEY + OPENAI_IMAGE_MODEL).
  none         - deshabilitado.
"""
from __future__ import annotations
from pathlib import Path
from urllib.parse import quote
import httpx
from core.config import settings, DATA_DIR
from core.storage import get_dir

IMAGE_DIR = get_dir("cinematic_images")

_MAX_IMAGE_BYTES = 25 * 1024 * 1024

class ImageProvider:
    def __init__(self):
        self.provider = (settings.image_provider or "pollinations").lower()

    def is_configured(self) -> bool:
        if self.provider == "none":
            return False
        if self.provider == "pollinations":
            return True  # gratis, sin key; requiere internet
        if self.provider == "openai":
            return bool(settings.openai_api_key)
        return False

    async def generate(self, prompt: str, filename: str, size: str = "1792x1024") -> Path:
        if not self.is_configured():
            raise RuntimeError(
                "Image provider no configurado. Opciones: "
                "IMAGE_PROVIDER=pollinations (gratis, sin key) u "
                "openai (OPENAI_API_KEY + OPENAI_IMAGE_MODEL)."
            )
        safe = "".join(c for c in filename if c.isalnum() or c in "-_")[:40] or "scene"
        out = IMAGE_DIR / f"{safe}.png"
        if self.provider == "pollinations":
            return await self._pollinations(prompt, out, size)
        return await self._openai(prompt, out, size)

    async def _pollinations(self, prompt: str, out: Path, size: str = "1792x1024") -> Path:
        w, h = 1792, 1024
        try:
            pw, ph = size.lower().split("x")
            w, h = max(256, min(2048, int(pw))), max(256, min(2048, int(ph)))
        except Exception:
            pass
        import random

        url = f"https://image.pollinations.ai/prompt/{quote(prompt[:1500])}"
        params = {"width": w, "height": h, "seed": random.randint(0, 999999), "model": "flux", "nologo": "true"}
        try:
            async with httpx.AsyncClient(timeout=180.0) as client:
                total = 0
                with open(out, "wb") as f:
                    async with client.stream("GET", url, params=params) as r:
                        r.raise_for_status()
                        async for chunk in r.aiter_bytes(1024 * 256):
                            total += len(chunk)
                            if total > _MAX_IMAGE_BYTES:
                                break
                            f.write(chunk)
            if total > _MAX_IMAGE_BYTES or out.stat().st_size < 5000:
                out.unlink(missing_ok=True)
                raise RuntimeError("Pollinations devolvió imagen vacía o gigante; reintentá.")
        except httpx.HTTPError as e:
            raise RuntimeError(f"Pollinations error: {str(e)[:300]}")
        return out

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
