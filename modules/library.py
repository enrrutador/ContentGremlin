"""
ContentGremlin - Library / History
Persists ideas, scripts, audio and videos for later reuse.
"""

from pathlib import Path
from typing import Any, Optional
import json
from datetime import datetime, timezone
from core.config import DATA_DIR

LIBRARY_FILE = DATA_DIR / "library.json"
LIBRARY_FILE.parent.mkdir(parents=True, exist_ok=True)


def _load() -> list[dict]:
    if LIBRARY_FILE.exists():
        try:
            with open(LIBRARY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def _save(items: list[dict]) -> None:
    with open(LIBRARY_FILE, "w", encoding="utf-8") as f:
        json.dump(items, f, indent=2, ensure_ascii=False)


def add_item(
    item_type: str,
    title: str,
    content: Any,
    meta: Optional[dict] = None,
) -> dict:
    items = _load()
    entry = {
        "id": f"{item_type}_{int(datetime.now(timezone.utc).timestamp()*1000)}",
        "type": item_type,
        "title": title,
        "content": content,
        "meta": meta or {},
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    items.insert(0, entry)
    items = items[:200]
    _save(items)
    return entry


def list_items(item_type: Optional[str] = None, limit: int = 50) -> list[dict]:
    items = _load()
    if item_type:
        items = [i for i in items if i.get("type") == item_type]
    return items[:limit]


def get_item(item_id: str) -> Optional[dict]:
    for item in _load():
        if item.get("id") == item_id:
            return item
    return None


def delete_item(item_id: str) -> bool:
    items = _load()
    new_items = [i for i in items if i.get("id") != item_id]
    if len(new_items) == len(items):
        return False
    _save(new_items)
    return True
