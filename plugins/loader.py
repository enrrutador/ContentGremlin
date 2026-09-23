"""Minimal plugin loader. Drop plugins/*.py with NAME and register(app_context)."""
from __future__ import annotations
import importlib.util
from pathlib import Path
from typing import Any

PLUGINS_DIR = Path(__file__).resolve().parent

def discover_plugins() -> list[dict[str, Any]]:
    found = []
    for path in sorted(PLUGINS_DIR.glob("*.py")):
        if path.name.startswith("_") or path.name == "loader.py":
            continue
        found.append({"name": path.stem, "path": str(path)})
    return found

def load_plugin(path: Path, app_context: dict | None = None) -> dict[str, Any]:
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if not spec or not spec.loader:
        raise RuntimeError(f"Cannot load plugin: {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    name = getattr(mod, "NAME", path.stem)
    if hasattr(mod, "register"):
        mod.register(app_context or {})
    return {"name": name, "module": path.stem, "loaded": True}

def load_all(app_context: dict | None = None) -> list[dict[str, Any]]:
    results = []
    for meta in discover_plugins():
        try:
            results.append(load_plugin(Path(meta["path"]), app_context))
        except Exception as e:
            results.append({"name": meta["name"], "loaded": False, "error": str(e)})
    return results
