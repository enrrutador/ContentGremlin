# Skill: Upload to YouTube

## Preconditions
- `GET /api/status` → youtube_configured
- Supervised: `explicit_approval: true` after user yes
- Autonomous: only if autonomous_upload_allowed

## Steps
Default privacy: **private**.
```json
POST /api/upload_video
{
  "video_path": "...",
  "title": "...",
  "description": "...",
  "tags": ["..."],
  "privacy": "private",
  "thumbnail_path": "...",
  "explicit_approval": true
}
```
Never upload without permission. Credentials: credentials/client_secrets.json
