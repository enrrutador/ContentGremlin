import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import providers.llm as llm_mod
from providers.llm import LLMProvider


class FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


class FakeAsyncClient:
    def __init__(self, payload):
        self.payload = payload
        self.requests = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    async def post(self, url, headers=None, json=None):
        self.requests.append({"url": url, "headers": headers, "json": json})
        return FakeResponse(self.payload)


def _mock_client(monkeypatch, payload):
    client = FakeAsyncClient(payload)
    monkeypatch.setattr(llm_mod.httpx, "AsyncClient", lambda *args, **kwargs: client)
    return client


def test_unconfigured_provider_returns_placeholder(monkeypatch):
    monkeypatch.setattr(llm_mod.settings, "openai_api_key", None)
    provider = LLMProvider()
    provider.preferred = "openai"
    result = asyncio.run(provider.generate("hola"))
    assert "LLM not configured" in result


def test_openai_generate(monkeypatch):
    monkeypatch.setattr(llm_mod.settings, "openai_api_key", "test-key")
    monkeypatch.setattr(llm_mod.settings, "openai_model", "gpt-test")
    client = _mock_client(monkeypatch, {"choices": [{"message": {"content": "respuesta"}}]})

    provider = LLMProvider()
    provider.preferred = "openai"
    result = asyncio.run(provider.generate("prompt", system="sistema"))

    assert result == "respuesta"
    sent = client.requests[0]
    assert sent["url"].endswith("/chat/completions")
    assert sent["json"]["model"] == "gpt-test"
    assert sent["json"]["messages"][0]["role"] == "system"


def test_anthropic_generate(monkeypatch):
    monkeypatch.setattr(llm_mod.settings, "anthropic_api_key", "test-key")
    _mock_client(monkeypatch, {"content": [{"text": "claude"}]})

    provider = LLMProvider()
    provider.preferred = "anthropic"
    assert asyncio.run(provider.generate("prompt")) == "claude"


def test_xai_generate(monkeypatch):
    monkeypatch.setattr(llm_mod.settings, "xai_api_key", "test-key")
    _mock_client(monkeypatch, {"choices": [{"message": {"content": "grok"}}]})

    provider = LLMProvider()
    provider.preferred = "xai"
    assert asyncio.run(provider.generate("prompt")) == "grok"


def test_ollama_generate_merges_system_prompt(monkeypatch):
    client = _mock_client(monkeypatch, {"response": "local"})

    provider = LLMProvider()
    provider.preferred = "ollama"
    result = asyncio.run(provider.generate("prompt", system="sistema"))

    assert result == "local"
    assert "sistema" in client.requests[0]["json"]["prompt"]


def test_preferred_provider_without_key_falls_back_to_placeholder(monkeypatch):
    monkeypatch.setattr(llm_mod.settings, "anthropic_api_key", None)
    provider = LLMProvider()
    provider.preferred = "anthropic"
    assert "LLM not configured" in asyncio.run(provider.generate("x"))
