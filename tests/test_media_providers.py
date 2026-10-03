import asyncio
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import providers.image as image_mod
import providers.video_gen as video_mod
from providers.image import ImageProvider
from providers.video_gen import VideoGenProvider


class FakeResponse:
    def __init__(self, payload=None, content=b"", status=200):
        self._payload = payload
        self.content = content
        self.status_code = status
        self.text = ""

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


class FakeHttpClient:
    def __init__(self, post_payload, get_content):
        self.post_payload = post_payload
        self.get_content = get_content
        self.posts = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    async def post(self, url, headers=None, json=None):
        self.posts.append({"url": url, "json": json})
        return FakeResponse(payload=self.post_payload)

    async def get(self, url):
        return FakeResponse(content=self.get_content)


def test_image_provider_requires_api_key(monkeypatch):
    monkeypatch.setattr(image_mod.settings, "openai_api_key", None)

    provider = ImageProvider()
    assert provider.provider == "openai"
    assert provider.is_configured() is False

    with pytest.raises(RuntimeError):
        asyncio.run(provider.generate("prompt", "scene"))


def test_image_generate_downloads_result_and_normalizes_size(monkeypatch, tmp_path):
    monkeypatch.setattr(image_mod.settings, "openai_api_key", "test-key")
    monkeypatch.setattr(image_mod.settings, "openai_image_model", "dall-e-3")
    monkeypatch.setattr(image_mod, "IMAGE_DIR", tmp_path)

    client = FakeHttpClient(post_payload={"data": [{"url": "http://img"}]}, get_content=b"PNGDATA")
    monkeypatch.setattr(image_mod.httpx, "AsyncClient", lambda *args, **kwargs: client)

    out = asyncio.run(ImageProvider().generate("prompt", "scene 1", size="unsupported"))

    assert out.read_bytes() == b"PNGDATA"
    body = client.posts[0]["json"]
    assert body["size"] == "1792x1024"
    assert body["prompt"] == "prompt"


def test_video_gen_defaults_to_none(monkeypatch):
    monkeypatch.setattr(video_mod.settings, "video_provider", "none")

    provider = VideoGenProvider()
    assert provider.is_configured() is False
    assert asyncio.run(provider.generate_clip("prompt", 5, "clip")) is None


def test_video_gen_requires_url_for_generic_provider(monkeypatch):
    monkeypatch.setattr(video_mod.settings, "video_provider", "generic_http")
    monkeypatch.setattr(video_mod.settings, "video_api_url", None)
    assert VideoGenProvider().is_configured() is False


def test_video_gen_generic_http_downloads_clip(monkeypatch, tmp_path):
    monkeypatch.setattr(video_mod.settings, "video_provider", "generic_http")
    monkeypatch.setattr(video_mod.settings, "video_api_url", "http://api/v1/generate")
    monkeypatch.setattr(video_mod.settings, "video_api_key", None)
    monkeypatch.setattr(video_mod, "CLIP_DIR", tmp_path)

    client = FakeHttpClient(post_payload={"video_url": "http://clip"}, get_content=b"MP4DATA")
    monkeypatch.setattr(video_mod.httpx, "AsyncClient", lambda *args, **kwargs: client)

    out = asyncio.run(VideoGenProvider().generate_clip("prompt", 3.0, "clip 1"))

    assert out.read_bytes() == b"MP4DATA"
    assert client.posts[0]["json"] == {"prompt": "prompt", "duration": 3.0}
