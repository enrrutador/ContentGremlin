import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from core.safety import originality_score, enforce_originality, jaccard

def test_jaccard_identical():
    assert jaccard("hola mundo canal youtube", "hola mundo canal youtube") == 1.0

def test_blocks_near_copy_title():
    ref = ["Cómo crecer en YouTube en 30 días con estos trucos secretos"]
    clone = "Cómo crecer en YouTube en 30 días con estos trucos secretos"
    report = originality_score(clone, ref)
    assert report["ok"] is False or report["risk"] in ("high", "medium")

def test_allows_original_angle():
    ref = ["Cómo crecer en YouTube en 30 días con estos trucos secretos"]
    original = "Errores de edición que hacen que tu audiencia abandone en el primer minuto"
    enforce_originality(original, ref)

def test_script_overlap_detection():
    ref_script = "Hoy te voy a mostrar el método exacto que usé para ganar mil suscriptores en una semana usando solo shorts y una estrategia de hashtags"
    copyish = ref_script + " y más tips"
    report = originality_score(copyish, [ref_script])
    assert report["max_lcs"] > 0.3 or report["max_ngram"] > 0.1

if __name__ == "__main__":
    test_jaccard_identical(); test_blocks_near_copy_title(); test_allows_original_angle(); test_script_overlap_detection(); print("OK")
