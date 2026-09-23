"""
ContentGremlin - Safety & Originality Layer
Mandatory checks. Not perfect, but no longer cosmetic-only.
"""

from __future__ import annotations

import re
from typing import Any, Optional


class SafetyError(Exception):
    pass


def _normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text, flags=re.UNICODE)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _tokens(text: str) -> set[str]:
    stop = {
        "el", "la", "los", "las", "un", "una", "de", "del", "en", "y", "o", "a", "que",
        "es", "por", "para", "con", "se", "su", "al", "lo", "como", "más", "pero",
        "the", "a", "an", "of", "and", "or", "to", "in", "on", "for", "is", "are",
        "this", "that", "with", "your", "you", "my", "how", "what", "why",
    }
    return {t for t in _normalize(text).split() if len(t) > 2 and t not in stop}


def jaccard(a: str, b: str) -> float:
    ta, tb = _tokens(a), _tokens(b)
    if not ta or not tb:
        return 0.0
    inter = len(ta & tb)
    union = len(ta | tb)
    return inter / union if union else 0.0


def longest_common_substring_ratio(a: str, b: str) -> float:
    wa = _normalize(a).split()
    wb = _normalize(b).split()
    if not wa or not wb:
        return 0.0
    m, n = len(wa), len(wb)
    prev = [0] * (n + 1)
    best = 0
    for i in range(1, m + 1):
        cur = [0] * (n + 1)
        for j in range(1, n + 1):
            if wa[i - 1] == wb[j - 1]:
                cur[j] = prev[j - 1] + 1
                best = max(best, cur[j])
        prev = cur
    denom = min(m, n)
    return best / denom if denom else 0.0


def ngram_overlap(a: str, b: str, n: int = 4) -> float:
    def grams(text: str) -> set[str]:
        words = _normalize(text).split()
        if len(words) < n:
            return set()
        return {" ".join(words[i : i + n]) for i in range(len(words) - n + 1)}

    ga, gb = grams(a), grams(b)
    if not ga or not gb:
        return 0.0
    return len(ga & gb) / min(len(ga), len(gb))


def originality_score(text: str, reference_snippets: Optional[list[str]] = None) -> dict[str, Any]:
    references = [r for r in (reference_snippets or []) if r and len(r.strip()) > 15]
    if not text or len(text.strip()) < 40:
        return {"ok": False, "reason": "too_short", "max_jaccard": 1.0, "max_lcs": 1.0, "max_ngram": 1.0, "risk": "high"}

    max_j = max_lcs = max_ng = 0.0
    worst_ref = None
    for ref in references:
        j = jaccard(text, ref)
        lcs = longest_common_substring_ratio(text, ref)
        ng = ngram_overlap(text, ref, n=4)
        if len(_normalize(text).split()) > 20:
            ng = max(ng, ngram_overlap(text, ref, n=5))
        if max(j, lcs, ng) >= max(max_j, max_lcs, max_ng):
            worst_ref = ref[:120]
        max_j, max_lcs, max_ng = max(max_j, j), max(max_lcs, lcs), max(max_ng, ng)

    risk, ok, reason = "low", True, None
    if max_ng >= 0.25 or max_lcs >= 0.45:
        ok, risk, reason = False, "high", "structural_or_phrase_overlap"
    elif max_j >= 0.55 and max_lcs >= 0.30:
        ok, risk, reason = False, "high", "high_token_and_sequence_overlap"
    elif max_j >= 0.40 or max_lcs >= 0.35 or max_ng >= 0.15:
        risk, reason = "medium", "moderate_similarity"
        if len(text.split()) > 80 and (max_ng >= 0.12 or max_lcs >= 0.30):
            ok, risk, reason = False, "high", "script_too_similar"

    return {
        "ok": ok, "reason": reason,
        "max_jaccard": round(max_j, 3), "max_lcs": round(max_lcs, 3),
        "max_ngram": round(max_ng, 3), "risk": risk, "worst_ref_preview": worst_ref,
    }


def enforce_originality(text: str, reference_snippets: Optional[list[str]] = None, *, strict: bool = True) -> dict[str, Any]:
    report = originality_score(text, reference_snippets)
    if not report["ok"] and strict:
        raise SafetyError(
            "Originality check failed "
            f"(risk={report['risk']}, jaccard={report['max_jaccard']}, "
            f"lcs={report['max_lcs']}, ngram={report['max_ngram']}, "
            f"reason={report['reason']}). Regenerate with a different angle."
        )
    if len(text.strip()) < 30 and strict:
        raise SafetyError("Generated content is too short.")
    return report


def can_upload(mode: str, autonomous_upload_allowed: bool, explicit_approval: bool = False) -> bool:
    if explicit_approval:
        return True
    if mode == "autonomous" and autonomous_upload_allowed:
        return True
    return False


def validate_analysis_request(channel_url: str) -> None:
    if not channel_url or not str(channel_url).strip():
        raise SafetyError("Channel URL / handle is required.")


def safety_report() -> dict[str, Any]:
    return {
        "rules_active": True,
        "can_be_disabled": False,
        "checks": ["token_jaccard", "longest_common_word_sequence", "ngram_overlap_4_5", "minimum_length", "upload_permission_gates"],
        "rules": [
            "Never copy scripts, titles or structure literally",
            "Only extract high-level patterns from reference channels",
            "Multi-signal originality checks on generations",
            "Upload only with explicit permission or Autonomous + prior consent",
            "No deceptive metadata or impersonation",
        ],
        "limitations": [
            "No embedding model by default (optional future upgrade)",
            "Cannot guarantee YouTube policy compliance",
            "Structural pattern copying can still slip through; human review recommended",
        ],
    }
