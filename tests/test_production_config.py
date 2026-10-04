"""Tests for production profile normalization."""
from core.config import normalize_production, _default_production


def test_normalize_production_defaults():
    p = normalize_production(None)
    assert p["visual_style"] == "faceless_stock"
    assert p["quality_bar"] == "publishable"
    assert 0 <= p["music"]["intensity"] <= 1


def test_normalize_production_clamps_enums():
    p = normalize_production(
        {"visual_style": "nope", "editing_pace": "warp", "quality_bar": "ultra"}
    )
    assert p["visual_style"] == "faceless_stock"
    assert p["editing_pace"] == "medium"
    assert p["quality_bar"] == "publishable"


def test_normalize_production_nested_merge():
    p = normalize_production({"music": {"intensity": 0.9}, "broll": {"source": "pexels"}})
    assert p["music"]["intensity"] == 0.9
    assert p["music"]["enabled"] is True
    assert p["broll"]["source"] == "pexels"


def test_default_production_keys():
    d = _default_production()
    for key in ("visual_style", "broll", "music", "avatar", "brand"):
        assert key in d
