# Skill: Efectos y transiciones

```http
GET /api/plugins
GET /api/agent/effects
```

## Aplicar efecto

```http
POST /api/timeline/effects
{
  "projectId": "...",
  "clipId": "...",
  "effectId": "effect.fade_in",
  "params": { "duration": 1 }
}
```

### IDs comunes

| effectId | Params |
|----------|--------|
| effect.fade_in / fade_out | duration |
| effect.blur | sigma |
| effect.brightness / contrast | amount |
| effect.scale | w, h |
| effect.crop | w, h, x, y |
| effect.sepia, hflip, vflip | — |
| effect.speed | factor |
| effect.volume | level |
| effect.loudnorm | — |
| effect.title | text, fontsize |

## Crossfade

```http
POST /api/timeline/transitions
{
  "projectId": "...",
  "fromClipId": "...",
  "toClipId": "...",
  "transitionId": "transition.crossfade",
  "duration": 1
}
```

## Keyframes opacidad

```http
POST /api/timeline/keyframes
{
  "projectId": "...",
  "clipId": "...",
  "keyframes": [
    { "t": 0, "opacity": 0 },
    { "t": 0.5, "opacity": 1 },
    { "t": 4.5, "opacity": 1 },
    { "t": 5, "opacity": 0 }
  ]
}
```
