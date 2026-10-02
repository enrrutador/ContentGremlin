import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import modules.uploader as uploader


def _supervised(monkeypatch):
    monkeypatch.setattr(uploader, "load_user_profile", lambda: {"autonomous_upload_allowed": False})
    monkeypatch.setattr(uploader.ModeManager, "current", staticmethod(lambda: "supervised"))


def test_upload_denied_in_supervised_without_approval(monkeypatch):
    _supervised(monkeypatch)
    with pytest.raises(PermissionError):
        uploader.upload_video("video.mp4", "titulo")


def test_upload_requires_youtube_credentials_with_approval(monkeypatch):
    _supervised(monkeypatch)
    monkeypatch.setattr(uploader, "is_youtube_configured", lambda: False)
    with pytest.raises(RuntimeError, match="YouTube API not configured"):
        uploader.upload_video("video.mp4", "titulo", explicit_approval=True)


def test_upload_fails_fast_when_video_missing(monkeypatch):
    _supervised(monkeypatch)
    monkeypatch.setattr(uploader, "is_youtube_configured", lambda: True)
    with pytest.raises(FileNotFoundError):
        uploader.upload_video("/inexistente/video.mp4", "titulo", explicit_approval=True)


def test_upload_allowed_by_mode_and_profile(monkeypatch):
    monkeypatch.setattr(uploader, "load_user_profile", lambda: {"autonomous_upload_allowed": True})
    monkeypatch.setattr(uploader.ModeManager, "current", staticmethod(lambda: "autonomous"))
    monkeypatch.setattr(uploader, "is_youtube_configured", lambda: True)
    with pytest.raises(FileNotFoundError):
        uploader.upload_video("/inexistente/video.mp4", "titulo")
