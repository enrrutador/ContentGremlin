import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import core.mode_manager as mm
from core.mode_manager import ModeManager


def test_current_delegates_to_config(monkeypatch):
    monkeypatch.setattr(mm, "get_active_mode", lambda: "autonomous")
    assert ModeManager.current() == "autonomous"


def test_set_rejects_invalid_mode():
    with pytest.raises(ValueError):
        ModeManager.set("turbo")


def test_set_valid_mode_delegates(monkeypatch):
    monkeypatch.setattr(mm, "set_mode", lambda mode: {"mode": mode})
    assert ModeManager.set("autonomous") == {"mode": "autonomous"}


def test_is_autonomous_and_supervised(monkeypatch):
    monkeypatch.setattr(mm, "get_active_mode", lambda: "autonomous")
    assert ModeManager.is_autonomous() is True
    assert ModeManager.is_supervised() is False

    monkeypatch.setattr(mm, "get_active_mode", lambda: "supervised")
    assert ModeManager.is_supervised() is True
    assert ModeManager.is_autonomous() is False


def test_requires_approval_in_supervised_mode(monkeypatch):
    monkeypatch.setattr(mm, "get_active_mode", lambda: "supervised")
    for step in ("ideas", "script", "video", "metadata", "upload"):
        assert ModeManager.requires_approval(step) is True
    assert ModeManager.requires_approval("status") is False


def test_requires_approval_in_autonomous_mode(monkeypatch):
    monkeypatch.setattr(mm, "get_active_mode", lambda: "autonomous")
    monkeypatch.setattr(mm, "load_user_profile", lambda: {"autonomous_upload_allowed": False})
    assert ModeManager.requires_approval("upload") is True
    assert ModeManager.requires_approval("ideas") is False

    monkeypatch.setattr(mm, "load_user_profile", lambda: {"autonomous_upload_allowed": True})
    assert ModeManager.requires_approval("upload") is False
