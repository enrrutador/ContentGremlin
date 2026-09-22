"""
ContentGremlin - Channel Analyzer
Extracts high-level patterns only. Never downloads full video content for copying.
"""

from typing import Any
import subprocess
import json
import re
from core.safety import validate_analysis_request


def _run_yt_dlp(url: str, extra_args: list[str] | None = None) -> dict:
    """Run yt-dlp and return JSON."""
    cmd = [
        "yt-dlp",
        "--dump-single-json",
        "--skip-download",
        "--playlist-end", "30",
        "--no-warnings",
    ]
    if extra_args:
        cmd.extend(extra_args)
    cmd.append(url)

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=90,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr[:500] or "yt-dlp failed")
        return json.loads(result.stdout)
    except FileNotFoundError:
        raise RuntimeError(
            "yt-dlp is not installed. Install it with: pip install yt-dlp"
        )
    except Exception as e:
        raise RuntimeError(f"Failed to analyze channel: {str(e)}")


def analyze_channel(channel_url: str) -> dict[str, Any]:
    """
    Analyze a YouTube channel and return high-level patterns.
    """
    validate_analysis_request(channel_url)

    if channel_url.startswith("@"):
        channel_url = f"https://www.youtube.com/{channel_url}"
    elif "youtube.com" not in channel_url and "youtu.be" not in channel_url:
        channel_url = f"https://www.youtube.com/@{channel_url.lstrip('@')}"

    data = _run_yt_dlp(channel_url)

    entries = data.get("entries") or []
    if not entries and data.get("id"):
        entries = [data]

    videos = []
    total_views = 0
    durations = []

    for entry in entries[:25]:
        if not entry:
            continue
        title = entry.get("title") or ""
        view_count = entry.get("view_count") or 0
        duration = entry.get("duration") or 0
        description = (entry.get("description") or "")[:300]

        videos.append({
            "title": title,
            "view_count": view_count,
            "duration_seconds": duration,
            "description_preview": description,
        })
        total_views += view_count
        if duration:
            durations.append(duration)

    avg_duration = int(sum(durations) / len(durations)) if durations else 0
    top_videos = sorted(videos, key=lambda v: v["view_count"], reverse=True)[:10]

    title_words = []
    for v in top_videos:
        words = re.findall(r"\b\w+\b", v["title"].lower())
        title_words.extend(words)

    from collections import Counter
    common_words = [w for w, c in Counter(title_words).most_common(15) if len(w) > 3]

    report = {
        "channel_url": channel_url,
        "channel_name": data.get("channel") or data.get("uploader") or data.get("title") or "Unknown",
        "total_videos_analyzed": len(videos),
        "average_duration_seconds": avg_duration,
        "average_duration_minutes": round(avg_duration / 60, 1) if avg_duration else 0,
        "top_videos": top_videos,
        "common_title_words": common_words,
        "patterns": {
            "preferred_length": f"~{round(avg_duration / 60)} minutes" if avg_duration else "unknown",
            "title_style_hints": common_words[:8],
            "note": "Only high-level patterns extracted. No full content was copied.",
        },
        "safety": {
            "content_downloaded": False,
            "literal_copy_possible": False,
        },
    }

    return report
