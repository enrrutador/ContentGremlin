# Skill: Status, modo y perfil

## 1. Estado del sistema

```http
GET /api/status
```

**Respuesta típica:**
```json
{
  "status": "online",
  "mode": "supervised",
  "niche": "",
  "llm_provider": "openai",
  "youtube_configured": false,
  "safety": { },
  "version": "0.1.0"
}
```

Usá esto **antes** del primer trabajo. Si `llm_provider` es `"not set"`, avisá al usuario que configure LLM.

## 2. Modo

```http
GET /api/mode

POST /api/set_mode
Content-Type: application/json

{ "mode": "supervised" }
```

Valores: `supervised` | `autonomous`.

| Modo | Ideas | Script | Video | Upload |
|------|-------|--------|-------|--------|
| supervised | mostrar y esperar | mostrar y esperar | mostrar paths | **siempre** pedir OK |
| autonomous | generar y seguir | generar y seguir | generar y seguir | solo si autonomous_upload_allowed **y** explicit_approval |

## 3. Perfil

```http
GET /api/profile

POST /api/profile
{
  "niche": "tech / curiosidades",
  "tone": "cercano y claro",
  "language": "es",
  "llm_provider": "openai",
  "autonomous_upload_allowed": false
}
```

## 4. Config pública

```http
GET /api/config/public
```

## Checklist de arranque

- [ ] `/api/status` → online
- [ ] modo correcto
- [ ] niche/language si el usuario los definió
- [ ] youtube_configured solo importa si va a subir
