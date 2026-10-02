import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import modules.editor_bridge as bridge


class FakeResponse:
    def __init__(self, status=200, payload=None):
        self.status_code = status
        self._payload = payload or {}

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


class FakeClient:
    def __init__(self, gets=None, posts=None):
        self.gets = list(gets or [])
        self.posts = list(posts or [])
        self.sent = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    async def get(self, url):
        return self.gets.pop(0)

    async def post(self, url, json=None):
        self.sent.append((url, json))
        return self.posts.pop(0)


def _patch_client(monkeypatch, client):
    monkeypatch.setattr(bridge.httpx, "AsyncClient", lambda *args, **kwargs: client)


def test_editor_health_ok_when_capabilities_available(monkeypatch):
    _patch_client(monkeypatch, FakeClient(gets=[FakeResponse(200, {"capabilities": True})]))
    result = asyncio.run(bridge.editor_health("http://editor"))
    assert result["ok"] is True
    assert result["capabilities"] is True


def test_editor_health_falls_back_to_root_check(monkeypatch):
    _patch_client(monkeypatch, FakeClient(gets=[FakeResponse(503), FakeResponse(200)]))
    result = asyncio.run(bridge.editor_health("http://editor"))
    assert result["ok"] is True
    assert result["status"] == 200


def test_editor_health_reports_unreachable_editor():
    result = asyncio.run(bridge.editor_health("http://127.0.0.1:59999"))
    assert result["ok"] is False
    assert "error" in result


def test_send_to_editor_builds_integration_body(monkeypatch):
    client = FakeClient(posts=[FakeResponse(200, {"projectId": "p1"})])
    _patch_client(monkeypatch, client)

    result = asyncio.run(
        bridge.send_to_editor(
            video_path="/v/main.mp4",
            media_paths=["/v/b.mp4"],
            name="Proyecto",
            crossfade=0.5,
            base_url="http://editor",
        )
    )

    url, body = client.sent[0]
    assert url == "http://editor/api/integrate/gremlin"
    assert body["videoPath"] == "/v/main.mp4"
    assert body["mediaPaths"] == ["/v/main.mp4", "/v/b.mp4"]
    assert body["crossfade"] == 0.5
    assert result["projectId"] == "p1"
