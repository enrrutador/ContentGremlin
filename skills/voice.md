# Skill: Voz (TTS)

```http
POST /api/generate_voice
Content-Type: application/json

{
  "text": "<script completo>",
  "filename": "ep01",
  "voice": null
}
```

## Respuesta

```json
{ "success": true, "audio_path": "/abs/path/audio.wav", "library_id": "..." }
```

Guardá `audio_path` absoluto.

Preferí `super_pipeline` si no necesitás control paso a paso.

## Errores

TTS no configurado → avisar API key / provider.
