import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core import storage


def test_get_dir_creates_every_known_kind(tmp_path):
    for kind in storage.known_kinds():
        directory = storage.get_dir(kind, base=tmp_path)
        assert directory.exists()
        assert tmp_path in directory.parents or directory == tmp_path


def test_get_dir_rejects_unknown_kind(tmp_path):
    with pytest.raises(ValueError, match="Unknown storage kind"):
        storage.get_dir("inventado", base=tmp_path)


def test_get_dir_uses_data_dir_by_default():
    from core.config import DATA_DIR
    assert storage.get_dir("audio") == DATA_DIR / "audio"


def test_modules_consume_centralized_storage():
    import modules.subtitles as subtitles
    import modules.thumbnail as thumbnails
    import modules.video_creator as video_creator
    import providers.image as image_provider
    import providers.tts as tts
    import providers.video_gen as video_gen

    assert video_creator.VIDEO_DIR.name == "videos"
    assert subtitles.SUB_DIR.name == "subtitles"
    assert thumbnails.THUMB_DIR.name == "thumbnails"
    assert tts.AUDIO_DIR.name == "audio"
    assert image_provider.IMAGE_DIR.name == "images"
    assert video_gen.CLIP_DIR.name == "clips"
