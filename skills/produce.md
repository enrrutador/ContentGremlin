# produce — publish-ready production engine

**Endpoint:** `POST /api/produce`  
**Async:** `POST /api/produce_async` → `GET /api/jobs/{job_id}`  
**Profile:** `GET/POST /api/production`

## When

After an approved script, when the user wants B-roll timeline + subtitles + music + QA instead of the legacy still template.

## Rules

1. Respect production profile (never hardcode niche/style).
2. If `qa.ok` is false and `quality_bar` is `publishable`, do not upload; report `qa.reasons`.
3. Upload still requires permission gates.

## Request

```json
{
  "script": "...",
  "title": "...",
  "voice": null,
  "skip_qa": false
}
```

## Pre-flight

```http
GET /api/broll/status
GET /api/music/status
GET /api/production
```
