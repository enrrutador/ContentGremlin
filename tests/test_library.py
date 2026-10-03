import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import modules.library as library


def _isolate(monkeypatch, tmp_path):
    monkeypatch.setattr(library, "LIBRARY_FILE", tmp_path / "library.json")


def test_add_list_get_delete(monkeypatch, tmp_path):
    _isolate(monkeypatch, tmp_path)
    entry = library.add_item("idea", "Titulo", {"a": 1})
    assert entry["type"] == "idea"
    assert library.get_item(entry["id"])["title"] == "Titulo"
    assert len(library.list_items()) == 1
    assert library.list_items(item_type="script") == []
    assert library.delete_item(entry["id"]) is True
    assert library.get_item(entry["id"]) is None
    assert library.delete_item("nope") is False


def test_list_returns_newest_first_and_respects_limit(monkeypatch, tmp_path):
    _isolate(monkeypatch, tmp_path)
    for i in range(3):
        library.add_item("idea", f"t{i}", i)
    items = library.list_items(limit=2)
    assert len(items) == 2
    assert items[0]["title"] == "t2"


def test_corrupt_library_file_is_recovered(monkeypatch, tmp_path):
    _isolate(monkeypatch, tmp_path)
    (tmp_path / "library.json").write_text("{not json", encoding="utf-8")
    assert library.list_items() == []
    assert library.get_item("x") is None


def test_meta_defaults_to_empty_dict(monkeypatch, tmp_path):
    _isolate(monkeypatch, tmp_path)
    assert library.add_item("audio", "a", "path")["meta"] == {}
