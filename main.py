"""
ContentGremlin - Main entry point
Run with: python main.py  or  ./start.sh
"""

import uvicorn
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from pathlib import Path

from api.routes import router
from core.config import settings, DATA_DIR, CREDENTIALS_DIR

DATA_DIR.mkdir(parents=True, exist_ok=True)
CREDENTIALS_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(
    title="ContentGremlin",
    description="Local toolkit for original YouTube content — agent-friendly API",
    version="0.1.0",
)
app.include_router(router, prefix="/api")

static_dir = Path(__file__).parent / "static"
templates_dir = Path(__file__).parent / "templates"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
templates = Jinja2Templates(directory=str(templates_dir)) if templates_dir.exists() else None


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    if templates is not None:
        try:
            return templates.TemplateResponse("index.html", {"request": request})
        except Exception:
            pass
    return HTMLResponse(
        "<h1>ContentGremlin</h1>"
        "<p>API online. Docs: <a href='/docs'>/docs</a></p>"
        "<p>Editor: <a href='http://127.0.0.1:3000'>localhost:3000</a></p>"
        "<p>Product path: docs/PRODUCT.md</p>"
    )


@app.get("/health")
async def health():
    return {"status": "ok", "service": "ContentGremlin", "editor_hint": "http://127.0.0.1:3000"}


if __name__ == "__main__":
    print(f"ContentGremlin API → http://127.0.0.1:{settings.port}")
    print("Editor → http://127.0.0.1:3000  (./start.sh levanta ambos)")
    print(f"OpenAPI → http://127.0.0.1:{settings.port}/docs")
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
