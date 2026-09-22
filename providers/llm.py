"""
ContentGremlin - LLM Provider abstraction
Supports multiple backends. User can choose their own.
"""

from typing import Optional
from core.config import settings, load_user_profile
import httpx


class LLMProvider:
    def __init__(self):
        profile = load_user_profile()
        self.preferred = profile.get("llm_provider", "openai")

    async def generate(self, prompt: str, system: Optional[str] = None, temperature: float = 0.7) -> str:
        provider = self.preferred

        if provider == "openai" and settings.openai_api_key:
            return await self._openai(prompt, system, temperature)
        elif provider == "anthropic" and settings.anthropic_api_key:
            return await self._anthropic(prompt, system, temperature)
        elif provider == "xai" and settings.xai_api_key:
            return await self._xai(prompt, system, temperature)
        elif provider == "ollama":
            return await self._ollama(prompt, system, temperature)
        else:
            return (
                "[LLM not configured] Please add at least one API key in the Configuration tab.\n\n"
                f"Prompt received:\n{prompt[:500]}..."
            )

    async def _openai(self, prompt: str, system: Optional[str], temperature: float) -> str:
        headers = {
            "Authorization": f"Bearer {settings.openai_api_key}",
            "Content-Type": "application/json",
        }
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": settings.openai_model,
            "messages": messages,
            "temperature": temperature,
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]

    async def _anthropic(self, prompt: str, system: Optional[str], temperature: float) -> str:
        headers = {
            "x-api-key": settings.anthropic_api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }
        payload = {
            "model": settings.anthropic_model,
            "max_tokens": 4096,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system:
            payload["system"] = system

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers=headers,
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            return data["content"][0]["text"]

    async def _xai(self, prompt: str, system: Optional[str], temperature: float) -> str:
        headers = {
            "Authorization": f"Bearer {settings.xai_api_key}",
            "Content-Type": "application/json",
        }
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": settings.xai_model,
            "messages": messages,
            "temperature": temperature,
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                "https://api.x.ai/v1/chat/completions",
                headers=headers,
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]

    async def _ollama(self, prompt: str, system: Optional[str], temperature: float) -> str:
        payload = {
            "model": settings.ollama_model,
            "prompt": prompt if not system else f"{system}\n\n{prompt}",
            "stream": False,
            "options": {"temperature": temperature},
        }
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"{settings.ollama_base_url}/api/generate",
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("response", "")
