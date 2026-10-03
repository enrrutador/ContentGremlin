"""
ContentGremlin - YouTube Uploader
Optional. Only works when YouTube Data API credentials are configured.
"""

from pathlib import Path
from typing import Optional, Any
import time
from core.config import settings, load_user_profile
from core.safety import can_upload
from core.mode_manager import ModeManager

RETRYABLE_HTTP_STATUS = {500, 502, 503, 504}
UPLOAD_CHUNK_SIZE = 8 * 1024 * 1024


def is_youtube_configured() -> bool:
    secrets = Path(settings.youtube_client_secrets_file)
    token = Path(settings.youtube_token_file)
    return secrets.exists() or token.exists()


def _get_youtube_service():
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
    except ImportError:
        raise RuntimeError(
            "Google API libraries not installed. Run: pip install google-api-python-client google-auth-oauthlib"
        )

    SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
    creds = None
    token_path = Path(settings.youtube_token_file)
    secrets_path = Path(settings.youtube_client_secrets_file)

    if token_path.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
        except Exception:
            creds = None

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not secrets_path.exists():
                raise RuntimeError(
                    f"YouTube credentials not found. Place client_secrets.json at: {secrets_path}"
                )
            flow = InstalledAppFlow.from_client_secrets_file(str(secrets_path), SCOPES)
            creds = flow.run_local_server(port=0)
        token_path.parent.mkdir(parents=True, exist_ok=True)
        token_path.write_text(creds.to_json(), encoding="utf-8")
        try:
            token_path.chmod(0o600)
        except Exception:
            pass

    return build("youtube", "v3", credentials=creds)


def _is_retryable(error: Exception) -> bool:
    status = getattr(getattr(error, "resp", None), "status", None)
    if status in RETRYABLE_HTTP_STATUS:
        return True
    if isinstance(error, (ConnectionError, TimeoutError, OSError)):
        return True
    return type(error).__name__ in {"ServerNotFoundError", "TransportError", "ProtocolError"}


def _resumable_upload(request, max_retries: int = 5, base_delay: float = 1.0) -> dict:
    """Drive a resumable upload to completion with exponential backoff.

    `next_chunk()` resumes from the last committed byte, so retrying is safe.
    """
    retries = 0
    response = None
    while response is None:
        try:
            _, response = request.next_chunk()
            retries = 0
        except Exception as error:
            if not _is_retryable(error) or retries >= max_retries:
                raise
            time.sleep(base_delay * (2 ** retries))
            retries += 1
    return response


def upload_video(
    video_path: str | Path,
    title: str,
    description: str = "",
    tags: Optional[list[str]] = None,
    category_id: str = "22",
    privacy: str = "private",
    thumbnail_path: Optional[str | Path] = None,
    explicit_approval: bool = False,
) -> dict[str, Any]:
    profile = load_user_profile()
    mode = ModeManager.current()
    if not can_upload(mode, profile.get("autonomous_upload_allowed", False), explicit_approval):
        raise PermissionError(
            "Upload not allowed. Switch to Autonomous mode with upload permission, "
            "or pass explicit_approval=True in Supervised mode."
        )

    if not is_youtube_configured():
        raise RuntimeError("YouTube API not configured. Add credentials via Configuration or .env")

    path = Path(video_path)
    if not path.exists():
        raise FileNotFoundError(f"Video not found: {path}")

    youtube = _get_youtube_service()

    body = {
        "snippet": {
            "title": title[:100],
            "description": description[:5000],
            "tags": (tags or [])[:30],
            "categoryId": category_id,
        },
        "status": {
            "privacyStatus": privacy,
            "selfDeclaredMadeForKids": False,
        },
    }

    from googleapiclient.http import MediaFileUpload

    media = MediaFileUpload(str(path), chunksize=UPLOAD_CHUNK_SIZE, resumable=True)
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

    response = _resumable_upload(request)

    video_id = response["id"]
    result = {
        "success": True,
        "video_id": video_id,
        "url": f"https://www.youtube.com/watch?v={video_id}",
        "privacy": privacy,
    }

    if thumbnail_path and Path(thumbnail_path).exists():
        try:
            youtube.thumbnails().set(
                videoId=video_id,
                media_body=MediaFileUpload(str(thumbnail_path)),
            ).execute()
            result["thumbnail_set"] = True
        except Exception as e:
            result["thumbnail_error"] = str(e)

    return result
