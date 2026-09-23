import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from modules.subtitles import _split_into_cues

def test_cues_cover_duration():
    text = "Uno. Dos. Tres. Cuatro. Cinco frases cortas para probar."
    cues = _split_into_cues(text, total_duration=20.0)
    assert cues and cues[0]["start"] == 0.0 and cues[-1]["end"] >= 19.0

def test_fallback_without_duration():
    assert len(_split_into_cues("Hola mundo. Segunda frase.")) >= 1

if __name__ == "__main__":
    test_cues_cover_duration(); test_fallback_without_duration(); print("OK")
