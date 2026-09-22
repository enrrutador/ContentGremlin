"""
ContentGremlin - TTS Provider
Supports OpenAI TTS and ElevenLabs (optional).
"""

from pathlib import Path
from typing import Optional
import httpx
from core.config import settings, load_user_profile, DATA_DIR

AUDIO_DIR = DATA_DIR / "audio"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)


class TTSProvider:
    def __init__(self):
        profile = load_user_profile()
        self.preferred = profile.get("tts_provider", "openai")

    async def generate(
        self,
        text: str,
        filename: Optional[str] = None,
        voice: Optional[str] = None,
    ) -> Path:
        if not text or len(text.strip()) < 10:
            raise ValueError("Text too short for TTS")

        safe_name = filename or "narration"
        safe_name = "".join(c for c in safe_name if c.isalnum() or c in "-_")[:60]
        out_path = AUDIO_DIR / f"{safe_name}.mp3"

        if self.preferred == "elevenlabs" and settings.elevenlabs_api_key:
            return await self._elevenlabs(text, out_path, voice)
        else:
            return await self._openai(text, out_path, voice)

    async def _openai(self, text: str, out_path: Path, voice: Optional[str]) -> Path:
        if not settings.openai_api_key:
            raise RuntimeError(
                "OpenAI API key not configured. Add OPENAI_API_KEY to .env or switch TTS provider."
            )

        voice = voice or settings.openai_tts_voice or "alloy"
        chunks = self._split_text(text, max_chars=4000)

        audio_bytes = await self._openai_single(chunks[0], voice)
        out_path.write_bytes(audio_bytes)
        return out_path

    async def _openai_single(self, text: str, voice: str) -> bytes:
        headers = {
            "Authorization": f"Bearer {settings.openai_api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "tts-1",
            "input": text,
            "voice": voice,
            "response_format": "mp3",
        }
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                "https://api.openai.com/v1/audio/speech",
                headers=headers,
                json=payload,
            )
            resp.raise_for_status()
            return resp.content

    async def _elevenlabs(self, text: str, out_path: Path, voice: Optional[str]) -> Path:
        voice_id = voice or "21m00Tcm4TlvDq8ikWAM"
        headers = {
            "xi-api-key": settings.elevenlabs_api_key,
            "Content-Type": "application/json",
        }
        payload = {
            "text": text[:5000],
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {"stability": 0.4, "similarity_boost": 0.8},
        }
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
                headers=headers,
                json=payload,
            )
            resp.raise_for_status()
            out_path.write_bytes(resp.content)
            return out_path

    def _split_text(self, text: str, max_chars: int = 4000) -> list[str]:
        if len(text) <= max_chars:
            return [text]
        chunks = []
        current = ""
        for sentence in text.replace("\n", " ").split(". "):
            if len(current) + len(sentence) + 2 > max_chars:
                if current:
                    chunks.append(current.strip())
                current = sentence + ". "
            else:
                current += sentence + ". "
        if current.strip():
            chunks.append(current.strip())
        return chunks or [text[:max_chars]]
