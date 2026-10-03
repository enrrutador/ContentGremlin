"""
ContentGremlin - Stock B-roll engine
Pexels (primary) + Pixabay (fallback) with relevance scoring, HD preference,
duration fit, disk cache and graceful degradation.
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any, Optional
import httpx

from core.config import settings
from core.storage import get_dir

BROLL_DIR = get_dir("broll")
CACHE_DIR = get_dir("broll_cache")

_STOP = {
    "the", "and", "for", "with", "you", "your", "this", "that", "from", "into",
    "el", "la", "los", "las", "de", "del", "en", "un", "una", "que", "por", "para",
    "con", "como", "más", "pero", "una", "unos", "what", "how", "why", "when",
    "very", "just", "about", "over", "under", "than", "then", "also",
}


def _keywords(text: str, max_terms: int = 6) -> str:
    words = re.findall(r"[a-záéíóúñüA-ZÁÉÍÓÚÑÜ0-9]+", (text or "").lower())
    filtered = [w for w in words if len(w) > 3 and w not in _STOP and not w.isdigit()]
    # prefer English-looking tokens for stock APIs
    return " ".join(filtered[:max_terms]) or "cinematic abstract"


def _cache_path(url: str, ext: str = ".mp4") -> Path:
    h = hashlib.sha256(url.encode("utf-8")).hexdigest()[:20]
    return CACHE_DIR / f"{h}{ext}"


async def _download(url: str, ext: str = ".mp4") -> Optional[Path]:
    dest = _cache_path(url, ext)
    if dest.exists() and dest.stat().st_size > 5000:
        return dest
    try:
        async with httpx.AsyncClient(timeout=90.0, follow_redirects=True) as client:
            r = await client.get(url)
            r.raise_for_status()
            dest.write_bytes(r.content)
        if dest.stat().st_size < 5000:
            dest.unlink(missing_ok=True)
            return None
        return dest
    except Exception:
        dest.unlink(missing_ok=True)
        return None


def _score_video_file(
    file_meta: dict,
    *,
    target_duration: float,
    prefer_hd: bool,
    prefer_vertical: bool,
) -> float:
    """Higher is better."""
    score = 0.0
    w = int(file_meta.get("width") or 0)
    h = int(file_meta.get("height") or 0)
    dur = float(file_meta.get("duration") or file_meta.get("duration_seconds") or 0)

    if prefer_hd:
        if w >= 1920 or h >= 1080:
            score += 30
        elif w >= 1280 or h >= 720:
            score += 20
        elif w >= 640:
            score += 8
    else:
        score += 10

    if prefer_vertical:
        if h > w:
            score += 25
        else:
            score -= 10
    else:
        if w >= h:
            score += 15

    if dur > 0 and target_duration > 0:
        ratio = dur / target_duration
        if 0.8 <= ratio <= 2.5:
            score += 20
        elif 0.5 <= ratio <= 4.0:
            score += 8
        else:
            score -= 5

    # prefer mp4/h264-ish links
    link = (file_meta.get("link") or file_meta.get("url") or "").lower()
    if ".mp4" in link:
        score += 5
    return score


async def _pexels_search(
    query: str,
    *,
    target_duration: float,
    prefer_hd: bool,
    prefer_vertical: bool,
) -> Optional[dict[str, Any]]:
    key = settings.pexels_api_key
    if not key:
        return None
    orientation = "portrait" if prefer_vertical else "landscape"
    params = {"query": query, "per_page": 12, "orientation": orientation}
    headers = {"Authorization": key}
    try:
        async with httpx.AsyncClient(timeout=25.0) as client:
            r = await client.get("https://api.pexels.com/videos/search", headers=headers, params=params)
            if r.status_code != 200:
                return None
            videos = r.json().get("videos") or []
    except Exception:
        return None

    best: Optional[tuple[float, dict, dict]] = None
    for v in videos:
        duration = float(v.get("duration") or 0)
        files = v.get("video_files") or []
        for f in files:
            meta = {
                "width": f.get("width"),
                "height": f.get("height"),
                "duration": duration,
                "link": f.get("link"),
            }
            sc = _score_video_file(meta, target_duration=target_duration, prefer_hd=prefer_hd, prefer_vertical=prefer_vertical)
            if best is None or sc > best[0]:
                best = (sc, v, f)
    if not best:
        return None
    _, video, file_meta = best
    link = file_meta.get("link")
    if not link:
        return None
    path = await _download(link, ".mp4")
    if not path:
        return None
    return {
        "provider": "pexels",
        "id": video.get("id"),
        "query": query,
        "path": str(path),
        "width": file_meta.get("width"),
        "height": file_meta.get("height"),
        "duration": video.get("duration"),
        "url": video.get("url"),
        "score": best[0],
    }


async def _pixabay_search(
    query: str,
    *,
    target_duration: float,
    prefer_hd: bool,
    prefer_vertical: bool,
) -> Optional[dict[str, Any]]:
    key = settings.pixabay_api_key
    if not key:
        return None
    params = {
        "key": key,
        "q": query,
        "video_type": "film",
        "per_page": 12,
        "safesearch": "true",
    }
    try:
        async with httpx.AsyncClient(timeout=25.0) as client:
            r = await client.get("https://pixabay.com/api/videos/", params=params)
            if r.status_code != 200:
                return None
            hits = r.json().get("hits") or []
    except Exception:
        return None

    best: Optional[tuple[float, dict, str]] = None
    for hit in hits:
        duration = float(hit.get("duration") or 0)
        videos = hit.get("videos") or {}
        # prefer medium/large
        for quality in ("large", "medium", "small", "tiny"):
            entry = videos.get(quality) or {}
            url = entry.get("url")
            if not url:
                continue
            meta = {
                "width": entry.get("width"),
                "height": entry.get("height"),
                "duration": duration,
                "link": url,
            }
            sc = _score_video_file(meta, target_duration=target_duration, prefer_hd=prefer_hd, prefer_vertical=prefer_vertical)
            if quality == "large":
                sc += 5
            if best is None or sc > best[0]:
                best = (sc, hit, url)
            break
    if not best:
        return None
    _, hit, url = best
    path = await _download(url, ".mp4")
    if not path:
        return None
    return {
        "provider": "pixabay",
        "id": hit.get("id"),
        "query": query,
        "path": str(path),
        "duration": hit.get("duration"),
        "score": best[0],
    }


async def fetch_clip_for_query(
    query: str,
    *,
    target_duration: float = 5.0,
    source: str = "mixed",
    prefer_hd: bool = True,
    prefer_vertical: bool = False,
) -> Optional[dict[str, Any]]:
    q = _keywords(query)
    clip = None
    if source in ("pexels", "mixed"):
        clip = await _pexels_search(q, target_duration=target_duration, prefer_hd=prefer_hd, prefer_vertical=prefer_vertical)
    if not clip and source in ("pixabay", "mixed"):
        clip = await _pixabay_search(q, target_duration=target_duration, prefer_hd=prefer_hd, prefer_vertical=prefer_vertical)
    return clip


async def fetch_broll_for_scenes(
    scenes: list[dict[str, Any]],
    broll_cfg: dict[str, Any],
) -> list[dict[str, Any]]:
    """Resolve one stock asset per scene. Missing assets marked type=missing."""
    source = broll_cfg.get("source", "mixed")
    prefer_hd = bool(broll_cfg.get("prefer_hd", True))
    prefer_vertical = bool(broll_cfg.get("prefer_vertical", False))
    results: list[dict[str, Any]] = []

    for scene in scenes:
        prompt = scene.get("visual_prompt") or scene.get("narration_excerpt") or ""
        dur = float(scene.get("duration_seconds") or 5.0)
        dur = max(
            float(broll_cfg.get("min_clip_seconds", 2.5)),
            min(float(broll_cfg.get("max_clip_seconds", 8.0)), dur),
        )
        clip = await fetch_clip_for_query(
            prompt,
            target_duration=dur,
            source=source,
            prefer_hd=prefer_hd,
            prefer_vertical=prefer_vertical,
        )
        if clip:
            results.append({
                "scene_index": scene.get("index"),
                "type": "stock",
                "query": clip.get("query"),
                "clip_path": clip["path"],
                "provider": clip.get("provider"),
                "duration_seconds": dur,
                "source_duration": clip.get("duration"),
                "score": clip.get("score"),
            })
        else:
            results.append({
                "scene_index": scene.get("index"),
                "type": "missing",
                "query": _keywords(prompt),
                "clip_path": None,
                "duration_seconds": dur,
            })
    return results


def broll_status() -> dict[str, Any]:
    return {
        "pexels_configured": bool(settings.pexels_api_key),
        "pixabay_configured": bool(settings.pixabay_api_key),
        "cache_dir": str(CACHE_DIR),
        "cache_files": len(list(CACHE_DIR.glob("*"))) if CACHE_DIR.exists() else 0,
    }
