# ContentGremlin – Agent Integration

ContentGremlin is designed from the ground up to be used by other AI agents (OpenClaw, Hermes, custom agents, etc.).

## How agents interact with it

1. Start ContentGremlin locally (`python main.py`).
2. The agent calls the REST API at `http://localhost:8000`.
3. Full interactive documentation is available at `http://localhost:8000/docs`.

## Recommended tool surface for agents

| Endpoint                  | Method | Purpose                              |
|---------------------------|--------|--------------------------------------|
| `/status`                 | GET    | Current mode, health, active profile |
| `/set_mode`               | POST   | Switch between supervised/autonomous |
| `/analyze_channel`        | POST   | Analyze a reference YouTube channel  |
| `/generate_ideas`         | POST   | Generate original ideas              |
| `/write_script`           | POST   | Write a full original script         |
| `/generate_voice`         | POST   | Generate narration                   |
| `/create_video`           | POST   | Assemble video + thumbnail           |
| `/generate_metadata`      | POST   | Titles, descriptions, tags           |
| `/upload_video`           | POST   | Upload (respects mode & permissions) |
| `/config/*`               | various| Read and update configuration        |

All responses are structured JSON so agents can reason about them easily.

## Authentication

By default the local instance is open (suitable for personal use).  
An optional API key system can be enabled from the Configuration tab for extra safety when exposing the service.

## Example flow for an autonomous agent

1. Check status
2. Set mode to `autonomous` (if allowed)
3. Analyze reference channel
4. Generate ideas
5. Pick the best idea (or let ContentGremlin choose according to profile)
6. Write script → voice → video → metadata
7. Upload

In supervised mode the agent should stop and wait for human approval signals at the critical steps.
