"""ContentGremlin - Channel Analyzer: high-level patterns from public metadata only."""
from __future__ import annotations
from typing import Any
import subprocess, json, re
from collections import Counter
from core.safety import validate_analysis_request

def _run_yt_dlp(url: str, extra_args: list[str] | None = None) -> dict:
    cmd = ["yt-dlp", "--dump-single-json", "--skip-download", "--playlist-end", "40", "--flat-playlist", "--no-warnings"]
    if extra_args: cmd.extend(extra_args)
    cmd.append(url)
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            cmd2 = ["yt-dlp", "--dump-single-json", "--skip-download", "--playlist-end", "30", "--no-warnings", url]
            result = subprocess.run(cmd2, capture_output=True, text=True, timeout=120)
            if result.returncode != 0:
                raise RuntimeError(result.stderr[:500] or "yt-dlp failed")
        return json.loads(result.stdout)
    except FileNotFoundError:
        raise RuntimeError("yt-dlp is not installed. Install: pip install yt-dlp")

def _classify_title_formula(title: str) -> str:
    t, tl = title.strip(), title.strip().lower()
    if re.search(r"\d+\s*(cosas|tips|formas|ways|reasons|errores|habits)", tl): return "listicle_number"
    if "?" in t: return "question"
    if re.search(r"\b(cómo|how to|como)\b", tl): return "howto"
    if re.search(r"\b(vs|versus)\b", tl): return "versus"
    if re.search(r"\b(2024|2025|2026)\b", tl): return "year_bait"
    if len(t) <= 35: return "short_punchy"
    return "statement"

def _hook_style_from_titles(titles: list[str]) -> list[str]:
    styles, joined = [], " ".join(titles).lower()
    if any("?" in t for t in titles[:10]): styles.append("questions_in_title")
    if re.search(r"\b(secret|secreto|nobody|nadie|truth|verdad)\b", joined): styles.append("curiosity_gap")
    if re.search(r"\b(i |yo |mi |my )\b", joined): styles.append("first_person")
    if re.search(r"\d+", joined): styles.append("numbers")
    return styles or ["plain_statement"]

def _duration_bucket(seconds: float) -> str:
    if seconds <= 0: return "unknown"
    m = seconds / 60
    if m < 1: return "shorts_under_1m"
    if m < 3: return "short_1_3m"
    if m < 8: return "mid_3_8m"
    if m < 15: return "long_8_15m"
    return "deep_15m_plus"

def analyze_channel(channel_url: str) -> dict[str, Any]:
    validate_analysis_request(channel_url)
    raw = channel_url.strip()
    if raw.startswith("@"): channel_url = f"https://www.youtube.com/{raw}"
    elif "youtube.com" not in raw and "youtu.be" not in raw: channel_url = f"https://www.youtube.com/@{raw.lstrip('@')}"
    else: channel_url = raw
    data = _run_yt_dlp(channel_url)
    entries = data.get("entries") or ([] if not data.get("id") else [data])
    videos, durations, views, formulas, word_counter, titles = [], [], [], Counter(), Counter(), []
    stop = {"the","and","for","with","you","your","this","that","from","el","la","los","las","de","del","en","un","una","que","por","para","con","como","más","pero","what","how","why"}
    for entry in entries[:30]:
        if not entry: continue
        title = (entry.get("title") or "").strip()
        if not title: continue
        view_count = entry.get("view_count") or 0
        duration = float(entry.get("duration") or 0)
        titles.append(title)
        formula = _classify_title_formula(title)
        formulas[formula] += 1
        if duration: durations.append(duration)
        if view_count: views.append(view_count)
        for w in re.findall(r"[a-záéíóúñüA-ZÁÉÍÓÚÑÜ0-9]+", title.lower()):
            if len(w) > 3 and w not in stop and not w.isdigit(): word_counter[w] += 1
        videos.append({"title": title, "view_count": view_count, "duration_seconds": duration, "duration_bucket": _duration_bucket(duration), "title_formula": formula, "url": entry.get("url") or entry.get("webpage_url") or "", "id": entry.get("id") or ""})
    ranked = sorted(videos, key=lambda v: v.get("view_count") or 0, reverse=True)
    top_titles = [v["title"] for v in ranked[:12]]
    avg_duration = sum(durations)/len(durations) if durations else 0
    avg_views = sum(views)/len(views) if views else 0
    median_duration = sorted(durations)[len(durations)//2] if durations else 0
    duration_buckets = Counter(v["duration_bucket"] for v in videos)
    dominant_length = duration_buckets.most_common(1)[0][0] if duration_buckets else "unknown"
    dominant_formula = formulas.most_common(1)[0][0] if formulas else "unknown"
    common_words = [w for w,_ in word_counter.most_common(20)]
    hooks = _hook_style_from_titles(titles[:15])
    patterns = {
        "dominant_title_formula": dominant_formula,
        "title_formula_distribution": dict(formulas),
        "dominant_length_bucket": dominant_length,
        "length_distribution": dict(duration_buckets),
        "hook_styles_signal": hooks,
        "avg_duration_seconds": round(avg_duration, 1),
        "median_duration_seconds": round(median_duration, 1),
        "avg_views": round(avg_views, 1) if avg_views else None,
        "common_topic_words": common_words,
        "suggested_script_minutes": max(3, min(15, int(round((median_duration or avg_duration or 480)/60)))),
        "content_posture": ("list-driven educational" if dominant_formula=="listicle_number" else "problem-solution howto" if dominant_formula=="howto" else "curiosity-led" if "curiosity_gap" in hooks else "mixed"),
    }
    return {
        "channel_url": channel_url,
        "channel_name": data.get("channel") or data.get("uploader") or data.get("title") or "unknown",
        "videos_analyzed": len(videos),
        "top_titles": top_titles,
        "videos_sample": ranked[:15],
        "patterns": patterns,
        "reference_titles_for_safety": top_titles,
        "disclaimer": "Patterns from public titles/metadata only. Do not copy titles or scripts.",
    }
