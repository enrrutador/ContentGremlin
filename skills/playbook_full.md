# Playbook: episodio completo (agente)

En **supervised**, pará en los checkpoints.

## A. Arranque

1. `GET /api/status`
2. `POST /api/set_mode` si hace falta
3. `POST /api/profile` si hay niche/idioma

## B. Referencia → idea → script

4. `POST /api/analyze_channel` `{ "channel_url": "..." }`
5. **Checkpoint supervised:** resumir patterns
6. `POST /api/generate_ideas` `{ "analysis_report", "count": 8 }`
7. **Checkpoint supervised:** elegir idea
8. `POST /api/write_script` `{ "idea": elegida }`
9. **Checkpoint supervised:** OK script

## C. Producción

10. `POST /api/super_pipeline` con script, title, open_in_editor según pedido
11. Cinemático solo si el usuario lo pidió (`cinematic_pipeline`)
12. **Checkpoint supervised:** video_path, metadata, editor_url

## D. Montaje opcional

13. Editor si hace falta (`video_editor/skills/playbook_assemble.md`)
14. Nuevo video_path del render

## E. Publicación

15. Confirmar privacy
16. `POST /api/upload_video` con `explicit_approval: true` solo si corresponde
17. Entregar URL YouTube

## Si falla a mitad

Reutilizá script/paths ya generados. `GET /api/library`. Editor caído ≠ pack Gremlin fallido.
