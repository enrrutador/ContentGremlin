# Roadmap Video Editor Local

## Fase 1 - MVP local funcional
- Importar medios, biblioteca
- Línea de tiempo multipista video/audio
- Cortes, recortes básicos
- Exportación con FFmpeg

## Fase 2 - API agente
- POST /api/projects
- POST /api/media/import
- POST /api/timeline/clips /cut /effects /transitions
- POST /api/render + GET /api/render/{jobId}
- Guardado en JSON compatible OpenTimelineIO

## Fase 3 - Sistema de plugins
- Manifiestos JSON con validación schema
- Categorías y parámetros tipados
- Ejecución local, sin subir vídeos

## Fase 4 - Catálogo 200 módulos
Importación 20, Edición 25, Efectos 30, Color 25, Audio 20, Títulos 20, Transiciones 15, IA 15, Exportación 15, QA 15

## Fase 5 - Avanzado
Proxies, subtítulos, keyframes, corrección color, GPU, IA opcional
