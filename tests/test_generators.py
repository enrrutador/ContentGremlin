import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import modules.idea_generator as idea_generator
import modules.metadata as metadata
import modules.scene_planner as scene_planner
import modules.script_writer as script_writer


class FakeLLM:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    async def generate(self, prompt, system=None, temperature=0.7):
        self.calls.append(prompt)
        return self.responses.pop(0)


def test_generate_ideas_filters_non_original(monkeypatch):
    ref = "Cómo crecer en YouTube en 30 días con estos trucos secretos"
    payload = {
        "ideas": [
            {"title": "Errores de edición que espantan a tu audiencia", "angle": "a", "hook": "h", "estimated_minutes": 7},
            {"title": ref, "angle": "copia", "hook": "h", "estimated_minutes": 7},
        ]
    }
    monkeypatch.setattr(idea_generator, "LLMProvider", lambda: FakeLLM([json.dumps(payload)]))

    ideas = asyncio.run(idea_generator.generate_ideas({"top_titles": [ref], "patterns": {}}, count=8))

    assert len(ideas) == 1
    assert ideas[0]["title"].startswith("Errores")
    assert "originality" in ideas[0]


def test_generate_ideas_handles_invalid_json(monkeypatch):
    monkeypatch.setattr(idea_generator, "LLMProvider", lambda: FakeLLM(["no json here"]))
    assert asyncio.run(idea_generator.generate_ideas({"top_titles": []})) == []


def test_write_script_strips_code_fences(monkeypatch):
    body = " ".join(["Narración original y concreta para el oyente"] * 20)
    llm = FakeLLM([f"```markdown\n{body}\n```"])
    monkeypatch.setattr(script_writer, "LLMProvider", lambda: llm)

    script = asyncio.run(script_writer.write_script({"title": "x"}))

    assert "```" not in script
    assert script.startswith("Narración original")


def test_write_script_retries_when_too_similar(monkeypatch):
    ref = (
        "Hoy te voy a mostrar el método exacto que usé para ganar mil suscriptores "
        "en una semana usando solo shorts y una estrategia de hashtags"
    )
    original = (
        "Una reflexión distinta sobre constancia y creatividad para canales "
        "pequeños que recién empiezan su camino"
    )
    llm = FakeLLM([ref, original])
    monkeypatch.setattr(script_writer, "LLMProvider", lambda: llm)

    script = asyncio.run(script_writer.write_script({"title": "x"}, reference_titles=[ref]))

    assert script == original
    assert len(llm.calls) == 2


def test_generate_metadata_parses_json(monkeypatch):
    payload = {
        "title": "Título optimizado",
        "description": "Descripción del video",
        "tags": ["uno", "dos"],
        "chapters": [{"time": "0:00", "label": "Intro"}],
    }
    monkeypatch.setattr(metadata, "LLMProvider", lambda: FakeLLM([json.dumps(payload)]))

    result = asyncio.run(metadata.generate_metadata("guion largo"))

    assert result["title"] == "Título optimizado"
    assert "Capítulos" in result["description"]
    assert result["chapter_block"].startswith("0:00 Intro")


def test_generate_metadata_falls_back_without_json(monkeypatch):
    monkeypatch.setattr(metadata, "LLMProvider", lambda: FakeLLM(["texto plano sin json"]))

    result = asyncio.run(metadata.generate_metadata("guion", idea={"title": "Idea"}))

    assert result["title"] == "Idea"
    assert result["chapters"][0]["label"] == "Inicio"


def test_plan_scenes_parses_and_clamps(monkeypatch):
    payload = {
        "scenes": [
            {"index": 1, "narration_excerpt": "a", "duration_seconds": 500, "visual_prompt": "p", "motion": "pan_left"},
            {"index": 2, "narration_excerpt": "b", "duration_seconds": 0.1, "visual_prompt": "q"},
        ]
    }
    monkeypatch.setattr(scene_planner, "LLMProvider", lambda: FakeLLM([json.dumps(payload)]))

    scenes = asyncio.run(scene_planner.plan_scenes("guion", max_scenes=5))

    assert [s["index"] for s in scenes] == [1, 2]
    assert scenes[0]["duration_seconds"] == 12.0
    assert scenes[1]["duration_seconds"] == 2.5
    assert scenes[0]["motion"] == "pan_left"
    assert scenes[1]["motion"] == "slow_zoom_in"


def test_plan_scenes_falls_back_to_script_split(monkeypatch):
    monkeypatch.setattr(scene_planner, "LLMProvider", lambda: FakeLLM(["no json"]))

    scenes = asyncio.run(scene_planner.plan_scenes("Uno. Dos. Tres. Cuatro.", max_scenes=4))

    assert 1 <= len(scenes) <= 4
    assert all(s["visual_prompt"] for s in scenes)


def test_plan_scenes_rescales_to_total_duration(monkeypatch):
    payload = {"scenes": [{"index": 1, "duration_seconds": 2.5, "visual_prompt": "p"}]}
    monkeypatch.setattr(scene_planner, "LLMProvider", lambda: FakeLLM([json.dumps(payload)]))

    scenes = asyncio.run(scene_planner.plan_scenes("g", total_duration_seconds=10, max_scenes=3))

    assert scenes[0]["duration_seconds"] == 10.0
