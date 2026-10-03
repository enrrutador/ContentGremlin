"""
ContentGremlin - TTS Provider
Supports OpenAI TTS and ElevenLabs (optional).
"""

from pathlib import Path
from typing import Optional
import subprocess
import tempfile
import httpx
from core.config import settings, load_user_profile, DATA_DIR
from core.storage import get_dir

AUDIO_DIR = get_dir("audio")


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

        if len(chunks) == 1:
            out_path.write_bytes(await self._openai_single(chunks[0], voice))
            return out_path

        with tempfile.TemporaryDirectory(prefix="gremlin_tts_") as tmp:
            parts = []
            for i, chunk in enumerate(chunks):
                part = Path(tmp) / f"part_{i:03d}.mp3"
                part.write_bytes(await self._openai_single(chunk, voice))
                parts.append(part)
            self._concat_audio(parts, out_path)
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
        chunks = self._split_text(text, max_chars=4500)

        if len(chunks) == 1:
            out_path.write_bytes(await self._elevenlabs_single(chunks[0], voice_id))
            return out_path

        with tempfile.TemporaryDirectory(prefix="gremlin_tts_") as tmp:
            parts = []
            for i, chunk in enumerate(chunks):
                part = Path(tmp) / f"part_{i:03d}.mp3"
                part.write_bytes(await self._elevenlabs_single(chunk, voice_id))
                parts.append(part)
            self._concat_audio(parts, out_path)
        return out_path

    async def _elevenlabs_single(self, text: str, voice_id: str) -> bytes:
        headers = {
            "xi-api-key": settings.elevenlabs_api_key,
            "Content-Type": "application/json",
        }
        payload = {
            "text": text,
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
            return resp.content

    def _concat_audio(self, parts: list[Path], out_path: Path) -> None:
        """Join chunked TTS output into a single MP3 (stream copy, no re-encode)."""
        list_file = out_path.parent / f".{out_path.stem}_concat.txt"
        lines = []
        for part in parts:
            escaped = str(part.resolve()).replace("'", "'\\''")
            lines.append(f"file '{escaped}'")
        list_file.write_text("\n".join(lines), encoding="utf-8")
        try:
            result = subprocess.run(
                ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(list_file), "-c", "copy", str(out_path)],
                capture_output=True, text=True, timeout=600,
            )
            if result.returncode != 0:
                raise RuntimeError(f"FFmpeg concat error: {result.stderr[:800]}")
        finally:
            list_file.unlink(missing_ok=True)

    def _split_text(self, text: str, max_chars: int = 4000) -> list[str]:
        if len(text) <= max_chars:
            return [text]
        chunks = []
        current = ""
        for sentence in text.replace("\n", " ").split(". "):
            piece = sentence + ". "
            if len(current) + len(piece) > max_chars:
                if current:
                    chunks.append(current.strip())
                while len(piece) > max_chars:
                    cut = piece.rfind(" ", 0, max_chars)
                    if cut <= 0:
                        cut = max_chars
                    head = piece[:cut].strip()
                    if head:
                        chunks.append(head)
                    piece = piece[cut:].lstrip()
                current = piece
            else:
                current += piece
        if current.strip():
            chunks.append(current.strip())
        return [c for c in chunks if c] or [text[:max_chars]]
