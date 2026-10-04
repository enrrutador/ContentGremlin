# produce — publish-ready production engine

**Endpoint:** `POST /api/produce`  
**Async:** `POST /api/produce_async` → `GET /api/jobs/{job_id}`  
**Profile:** `GET/POST /api/production`

## When

After an approved script, when the user wants B-roll timeline + subtitles + music + QA instead of the legacy still template.

## Rules

1. Respect production profile (never hardcode niche/style).
2. El sistema informa, el usuario decide: `success:true` entrega el video siempre;
   mirá `publishable` + `qa.reasons` y **vos** decidís si se sube. Solo `strict_qa:true`
   voltea `success` a false cuando no pasa la barra.
3. Upload still requires permission gates.

## Request

```json
{
  "script": "...",
  "title": "...",
  "voice": null,
  "skip_qa": false,
  "strict_qa": false
}
```

## Pre-flight

```http
GET /api/broll/status
GET /api/music/status
GET /api/production
```
