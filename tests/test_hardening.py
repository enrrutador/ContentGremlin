"""Hardening 2+3: thumbnail escape, cinematic filters, jobs prune robusto."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import core.jobs as jobs
from modules.cinematic import _motion_filter
from modules.video_creator import _escape_drawtext


def test_thumbnail_escape_matches_video_creator():
    # thumbnail.py usa el mismo escape que video_creator (coma, punto y coma, corchetes)
    assert _escape_drawtext("a,b;c[d]e:f'g\"h\\i\nj") == "a\\,b\\;c\\[d\\]e\\:fgh\\\\i j"


def test_cinematic_motion_filters_cover_all_motions():
    for motion in ("slow_zoom_out", "pan_left", "pan_right", "static", "slow_zoom_in", "otro"):
        vf = _motion_filter(motion, 5.0)
        assert isinstance(vf, str) and len(vf) > 10
        assert "fps=30" in vf or "scale=" in vf


def test_execute_job_pruned_does_not_raise():
    job = jobs.create_job("t")
    del jobs._jobs[job["id"]]
    out = jobs._execute_job(job["id"], lambda: {"ok": 1})
    assert out["status"] == "failed"
    assert "pruned" in out["error"]


def test_create_thumbnail_escapes_special_chars(monkeypatch, tmp_path):
    import modules.thumbnail as thumb

    captured = {}
    monkeypatch.setattr(thumb, "THUMB_DIR", tmp_path)

    def fake_run(cmd, **kwargs):
        captured["vf"] = cmd[cmd.index("-vf") + 1]
        # El último arg es el out real (THUMB_DIR/<safe>.jpg)
        Path(cmd[-1]).write_bytes(b"x")

        class R:
            returncode = 0
            stderr = ""

        return R()

    import subprocess

    monkeypatch.setattr(subprocess, "run", fake_run)
    out = thumb.create_thumbnail("a,b;c[d]e:f'g", output_name="t1")
    assert out.exists()
    vf = captured["vf"]
    assert "\\," in vf and "\\;" in vf and "\\[" in vf and "\\:" in vf
