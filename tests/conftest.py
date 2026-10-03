"""Aisla archivos reales de data/ para que pytest nunca contamine al usuario."""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import core.jobs as jobs
import modules.library as library


@pytest.fixture(autouse=True)
def _isolate_data_files(monkeypatch, tmp_path):
    """Redirige library.json y jobs.json a tmp por defecto.

    Los tests que ya aíslan (test_library, test_jobs) simplemente re-parchean
    al mismo tmp, sin conflicto.
    """
    monkeypatch.setattr(library, "LIBRARY_FILE", tmp_path / "library.json")
    monkeypatch.setattr(jobs, "JOBS_FILE", tmp_path / "jobs.json")
    jobs._jobs.clear()
    yield
    jobs._jobs.clear()
