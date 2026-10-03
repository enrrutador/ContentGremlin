import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import core.config as config


def _patch_profile_path(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    monkeypatch.setattr(config, "PROFILE_FILE", tmp_path / "user_profile.json")


def test_settings_exposes_cinematic_fields():
    s = config.Settings(_env_file=None)
    assert s.image_provider == "openai"
    assert s.openai_image_model
    assert s.video_provider == "none"
    assert s.video_api_url is None
    assert s.cinematic_max_scenes == 12
    assert s.cinematic_default_style


def test_settings_uses_pydantic_v2_config():
    assert config.Settings.model_config.get("extra") == "ignore"
    assert "Config" not in config.Settings.__dict__


def test_load_user_profile_creates_defaults(monkeypatch, tmp_path):
    _patch_profile_path(monkeypatch, tmp_path)
    profile = config.load_user_profile()
    assert profile["mode"] == "supervised"
    assert profile["autonomous_upload_allowed"] is False
    assert (tmp_path / "user_profile.json").exists()


def test_save_and_load_roundtrip(monkeypatch, tmp_path):
    _patch_profile_path(monkeypatch, tmp_path)
    config.save_user_profile({"mode": "autonomous", "niche": "tech"})
    assert config.load_user_profile()["niche"] == "tech"
    assert config.get_active_mode() == "autonomous"


def test_set_mode_updates_profile(monkeypatch, tmp_path):
    _patch_profile_path(monkeypatch, tmp_path)
    updated = config.set_mode("autonomous")
    assert updated["mode"] == "autonomous"
    assert config.get_active_mode() == "autonomous"


def test_load_user_profile_survives_corrupt_json(monkeypatch, tmp_path):
    _patch_profile_path(monkeypatch, tmp_path)
    (tmp_path / "user_profile.json").write_text("{not json", encoding="utf-8")
    profile = config.load_user_profile()
    assert profile["mode"] == "supervised"
