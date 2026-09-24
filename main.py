"""ContentGremlin - Main entry. Run: python main.py | ./start.sh"""

import uvicorn
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pathlib import Path

from api.routes import router
from core.config import settings, DATA_DIR, CREDENTIALS_DIR

DATA_DIR.mkdir(parents=True, exist_ok=True)
CREDENTIALS_DIR.mkdir(parents=True, exist_ok=True)

ROOT = Path(__file__).parent
app = FastAPI(
    title="ContentGremlin",
    description="Local toolkit for original YouTube content — agent-friendly API",
    version="0.2.0",
)
app.include_router(router, prefix="/api")

static_dir = ROOT / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

templates_dir = ROOT / "templates"


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    index = templates_dir / "index.html"
    if index.exists():
        return HTMLResponse(index.read_text(encoding="utf-8"))
    return HTMLResponse(
        "<h1>ContentGremlin</h1><p><a href='/docs'>/docs</a> · "
        "<a href='http://127.0.0.1:3000'>Editor :3000</a></p>"
    )


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "ContentGremlin",
        "version": "0.2.0",
        "editor": "http://127.0.0.1:3000",
    }


if __name__ == "__main__":
    print(f"ContentGremlin shell → http://127.0.0.1:{settings.port}")
    print("Editor → http://127.0.0.1:3000")
    print(f"OpenAPI → http://127.0.0.1:{settings.port}/docs")
    uvicorn.run("main:app", host=settings.host, port=settings.port, reload=settings.debug)
