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

## Providers (`tts_provider` en perfil)

| Provider | Costo | Key | Notas |
|----------|-------|-----|-------|
| `edge` | gratis | no | Default sugerido. Voces Microsoft (`EDGE_TTS_VOICE`, ej `es-AR-TomasNeural`). Requiere internet. |
| `openai` | pago | `OPENAI_API_KEY` | Voz `openai_tts_voice` (ej `alloy`). |
| `elevenlabs` | pago | `ELEVENLABS_API_KEY` | Más natural. |

## Errores

TTS no configurado → avisar API key / provider.
