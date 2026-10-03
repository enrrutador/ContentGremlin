"""
ContentGremlin - Centralized storage
Single place for every writable directory. Modules call get_dir() instead
of re-implementing mkdir logic on their own.
"""

from __future__ import annotations
from pathlib import Path
from typing import Optional

from core.config import DATA_DIR

_KINDS = {
    "audio": ("audio",),
    "videos": ("videos",),
    "subtitles": ("subtitles",),
    "thumbnails": ("thumbnails",),
    "cinematic_images": ("cinematic", "images"),
    "cinematic_clips": ("cinematic", "clips"),
    "cinematic_scenes": ("cinematic", "scenes"),
    "cinematic_out": ("cinematic", "out"),
}


def get_dir(kind: str, base: Optional[Path] = None) -> Path:
    """Return (and create) the directory for a storage kind.

    `base` is mainly for tests: pass a tmp dir to isolate writes.
    """
    if kind not in _KINDS:
        raise ValueError(f"Unknown storage kind: {kind}. Valid: {sorted(_KINDS)}")
    root = base if base is not None else DATA_DIR
    path = root.joinpath(*_KINDS[kind])
    path.mkdir(parents=True, exist_ok=True)
    return path


def known_kinds() -> list[str]:
    return sorted(_KINDS)
