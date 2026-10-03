import asyncio
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import api.routes as routes
from core import __version__


def test_status_endpoint_reports_core_version(monkeypatch):
    monkeypatch.setattr(routes, "load_user_profile", lambda: {"niche": ""})
    monkeypatch.setattr(routes.ModeManager, "current", staticmethod(lambda: "supervised"))
    status = asyncio.run(routes.get_status())
    assert status["version"] == __version__


def test_agent_skills_reports_core_version():
    skills = asyncio.run(routes.api_agent_skills())
    assert skills["version"] == __version__


def test_main_app_uses_core_version():
    try:
        import main
    except ImportError:
        pytest.skip("uvicorn not installed")
    assert main.app.version == __version__
    assert asyncio.run(main.health())["version"] == __version__
