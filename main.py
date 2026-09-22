"""
ContentGremlin - Main entry point
Run with: python main.py
"""

import uvicorn
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from pathlib import Path

from api.routes import router
from core.config import settings, DATA_DIR, CREDENTIALS_DIR

# Ensure directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
CREDENTIALS_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(
    title="ContentGremlin",
    description="A mischievous little gremlin that studies successful YouTube channels and forges original content.",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# API routes
app.include_router(router, prefix="/api")

# Static & templates
BASE_DIR = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=BASE_DIR / "ui" / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "ui" / "templates")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/health")
async def health():
    return {"status": "ok", "service": "ContentGremlin"}


if __name__ == "__main__":
    print(f"""
╔══════════════════════════════════════════════════════╗
║             ContentGremlin v0.1.0                    ║
║  The mischievous content forging gremlin             ║
╠══════════════════════════════════════════════════════╣
║  Local interface → http://localhost:{settings.port}            ║
║  API docs        → http://localhost:{settings.port}/docs       ║
╚══════════════════════════════════════════════════════╝
    """)
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
