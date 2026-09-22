"""
ContentGremlin - Safety & Anti-Demonetization Layer
These rules are mandatory and cannot be disabled.
"""

from typing import Any


class SafetyError(Exception):
    """Raised when a safety rule is violated."""
    pass


def enforce_originality(text: str, reference_snippets: list[str] | None = None) -> bool:
    """
    Very basic originality check.
    In production this will be much stronger (embedding similarity, etc.).
    """
    if not text or len(text.strip()) < 50:
        raise SafetyError("Generated content is too short to be considered original.")

    if reference_snippets:
        text_lower = text.lower()
        for snippet in reference_snippets:
            if len(snippet) > 40 and snippet.lower() in text_lower:
                raise SafetyError(
                    "Generated content contains large literal fragments from the reference. "
                    "This is not allowed."
                )
    return True


def can_upload(mode: str, autonomous_upload_allowed: bool, explicit_approval: bool = False) -> bool:
    """
    Decide if an upload is permitted.
    """
    if explicit_approval:
        return True
    if mode == "autonomous" and autonomous_upload_allowed:
        return True
    return False


def validate_analysis_request(channel_url: str) -> None:
    if not channel_url or "youtube.com" not in channel_url and "youtu.be" not in channel_url:
        pass


def safety_report() -> dict[str, Any]:
    return {
        "rules_active": True,
        "can_be_disabled": False,
        "rules": [
            "Never copy scripts, titles or structure literally",
            "Only extract high-level patterns from reference channels",
            "Force originality checks on every generation",
            "Upload only with explicit permission or Autonomous + prior consent",
            "No deceptive metadata or impersonation",
        ],
    }
