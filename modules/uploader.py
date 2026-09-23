"""
ContentGremlin - YouTube Uploader
Optional. Only works when YouTube Data API credentials are configured.
"""

from pathlib import Path
from typing import Optional, Any
from core.config import settings, load_user_profile
from core.safety import can_upload
from core.mode_manager import ModeManager


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
        import pickle
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
            with open(token_path, "rb") as f:
                creds = pickle.load(f)
        except Exception:
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
        with open(token_path, "wb") as f:
            pickle.dump(creds, f)

    return build("youtube", "v3", credentials=creds)


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

    media = MediaFileUpload(str(path), chunksize=-1, resumable=True)
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    while response is None:
        status, response = request.next_chunk()

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
