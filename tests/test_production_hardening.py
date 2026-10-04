"""Hardening del production engine: sin red, sin keys, sin ffmpeg real."""

import asyncio
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import modules.broll as broll
import modules.production_engine as pe
import modules.qa_agent as qa
from core.config import settings


def test_produce_rejects_short_script():
    with pytest.raises(ValueError, match="too short"):
        asyncio.run(pe.produce(script="hola", title="t"))


def test_new_work_dir_unique_and_prunes_old(monkeypatch, tmp_path):
    monkeypatch.setattr(pe, "WORK_DIR", tmp_path)
    old = tmp_path / "job_viejo"
    old.mkdir()
    ancient = time.time() - 25 * 3600
    import os

    os.utime(old, (ancient, ancient))
    a = pe._new_work_dir()
    b = pe._new_work_dir()
    assert a != b and a.exists() and b.exists()
    assert not old.exists()


def test_broll_search_without_keys_returns_none(monkeypatch):
    monkeypatch.setattr(settings, "pexels_api_key", None)
    monkeypatch.setattr(settings, "pixabay_api_key", None)
    assert asyncio.run(broll._pexels_search("cocina", target_duration=5, prefer_hd=True, prefer_vertical=False)) is None
    assert asyncio.run(broll._pixabay_search("cocina", target_duration=5, prefer_hd=True, prefer_vertical=False)) is None


def test_broll_download_caps_huge_files(monkeypatch, tmp_path):
    monkeypatch.setattr(broll, "CACHE_DIR", tmp_path)

    class FakeHead:
        headers = {"content-length": str(600 * 1024 * 1024)}

    class FakeClient:
        def __init__(self, *a, **k):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def head(self, *a, **k):
            return FakeHead()

        def stream(self, *a, **k):
            raise AssertionError("no debe descargar si el HEAD ya excede el tope")

    import httpx

    monkeypatch.setattr(httpx, "AsyncClient", FakeClient)
    assert asyncio.run(broll._download("https://ejemplo.test/gigante.mp4")) is None


def test_qa_missing_file_not_publishable():
    out = qa.run_qa("/no/existe/video.mp4")
    assert out["publishable"] is False
    assert "video_file_missing" in out["reasons"]


def test_qa_gate_user_decides_by_default():
    from modules.production_engine import _apply_qa_gate

    failed_qa = {"ok": False, "publishable": False, "score": 0.65, "reasons": ["too_short"]}
    prod = {"quality_bar": "publishable"}
    out = _apply_qa_gate({"success": True}, failed_qa, prod)
    assert out["success"] is True
    assert out["publishable"] is False
    assert "too_short" in out["message"]


def test_qa_gate_strict_fails():
    from modules.production_engine import _apply_qa_gate

    failed_qa = {"ok": False, "publishable": False, "score": 0.65, "reasons": ["too_short"]}
    prod = {"quality_bar": "publishable"}
    out = _apply_qa_gate({"success": True}, failed_qa, prod, strict_qa=True)
    assert out["success"] is False
    assert out["publishable"] is False


def test_qa_gate_passing_qa_untouched():
    from modules.production_engine import _apply_qa_gate

    ok_qa = {"ok": True, "publishable": True, "score": 0.95, "reasons": []}
    out = _apply_qa_gate({"success": True}, ok_qa, {"quality_bar": "publishable"})
    assert out["success"] is True and out["publishable"] is True
    assert "message" not in out


def test_produce_endpoint_validates_script():
    from fastapi.testclient import TestClient
    from main import app

    c = TestClient(app)
    r = c.post("/api/produce", json={"script": "corto", "title": "t"})
    assert r.status_code == 400


def test_qa_endpoint_rejects_non_video():
    from fastapi.testclient import TestClient
    from main import app

    c = TestClient(app)
    r = c.post("/api/qa", json={"video_path": "/etc/passwd"})
    assert r.status_code == 400
