import asyncio
import os
import time

import edge_tts

from backend.services import tts


class FakeCommunicate:
    """Stand-in for edge_tts.Communicate that 'saves' a tiny fake mp3 file."""

    created = []

    def __init__(self, text, voice):
        FakeCommunicate.created.append((text, voice))

    async def save(self, path):
        with open(path, "wb") as audio_file:
            audio_file.write(b"fake-mp3-bytes")


def _use_fake_speech(monkeypatch, tmp_path):
    FakeCommunicate.created = []
    monkeypatch.setattr(edge_tts, "Communicate", FakeCommunicate)

    audio_dir = tmp_path / "audio_cache"
    monkeypatch.setattr(tts, "AUDIO_DIR", str(audio_dir))

    return audio_dir


def test_generate_speech_saves_an_mp3_and_creates_the_folder(monkeypatch, tmp_path):
    audio_dir = _use_fake_speech(monkeypatch, tmp_path)

    path = asyncio.run(tts.generate_speech("Namaste!"))

    assert path.startswith(str(audio_dir))
    assert path.endswith(".mp3")

    with open(path, "rb") as audio_file:
        assert audio_file.read() == b"fake-mp3-bytes"


def test_generate_speech_uses_the_voice_for_the_language(monkeypatch, tmp_path):
    _use_fake_speech(monkeypatch, tmp_path)

    asyncio.run(tts.generate_speech("Namaste", language="hi"))

    assert FakeCommunicate.created == [("Namaste", "hi-IN-SwaraNeural")]


def test_generate_speech_falls_back_to_default_voice(monkeypatch, tmp_path):
    _use_fake_speech(monkeypatch, tmp_path)

    asyncio.run(tts.generate_speech("Hello", language="not-a-language"))

    assert FakeCommunicate.created == [("Hello", "en-US-AriaNeural")]


def test_identical_speech_reuses_cached_file(monkeypatch, tmp_path):
    _use_fake_speech(monkeypatch, tmp_path)

    first = asyncio.run(tts.generate_speech("Hello"))
    second = asyncio.run(tts.generate_speech("Hello"))

    assert first == second
    assert FakeCommunicate.created == [("Hello", "en-US-AriaNeural")]


def test_different_text_creates_different_cache_files(monkeypatch, tmp_path):
    _use_fake_speech(monkeypatch, tmp_path)

    first = asyncio.run(tts.generate_speech("One"))
    second = asyncio.run(tts.generate_speech("Two"))

    assert first != second
    assert len(FakeCommunicate.created) == 2


def test_different_voice_creates_different_cache_files(monkeypatch, tmp_path):
    _use_fake_speech(monkeypatch, tmp_path)

    english = asyncio.run(tts.generate_speech("Hello", language="en"))
    hindi = asyncio.run(tts.generate_speech("Hello", language="hi"))

    assert english != hindi
    assert FakeCommunicate.created == [
        ("Hello", "en-US-AriaNeural"),
        ("Hello", "hi-IN-SwaraNeural"),
    ]


def test_expired_audio_files_are_removed(monkeypatch, tmp_path):
    audio_dir = _use_fake_speech(monkeypatch, tmp_path)

    expired_file = audio_dir / "expired.mp3"
    fresh_file = audio_dir / "fresh.mp3"

    audio_dir.mkdir(parents=True, exist_ok=True)
    expired_file.write_bytes(b"old")
    fresh_file.write_bytes(b"new")

    expired_time = time.time() - tts.AUDIO_CACHE_TTL - 1
    os.utime(expired_file, (expired_time, expired_time))

    asyncio.run(tts.generate_speech("Hello"))

    assert not expired_file.exists()
    assert fresh_file.exists()
