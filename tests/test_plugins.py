import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from plugins import loader


def test_discover_finds_example_plugin_and_skips_loader():
    names = {p["name"] for p in loader.discover_plugins()}
    assert "example_hello" in names
    assert "loader" not in names


def test_load_all_registers_plugins():
    context = {}
    results = loader.load_all(context)
    loaded = {r["name"]: r for r in results}
    assert loaded["example_hello"]["loaded"] is True
    assert "example_hello" in context.get("plugins_registered", [])


def test_load_all_isolates_broken_plugins(monkeypatch, tmp_path):
    (tmp_path / "broken.py").write_text("raise RuntimeError('boom')", encoding="utf-8")
    (tmp_path / "ok.py").write_text("NAME = 'ok'\n\ndef register(ctx):\n    ctx['ok'] = True\n", encoding="utf-8")
    monkeypatch.setattr(loader, "PLUGINS_DIR", tmp_path)

    context = {}
    by_name = {r["name"]: r for r in loader.load_all(context)}
    assert by_name["broken"]["loaded"] is False
    assert "boom" in by_name["broken"]["error"]
    assert by_name["ok"]["loaded"] is True
    assert context["ok"] is True
