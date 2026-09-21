import asyncio

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
    audio_dir = tmp_path / "audio_cache"  # does not exist yet on purpose
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


def test_each_call_writes_a_new_file(monkeypatch, tmp_path):
    _use_fake_speech(monkeypatch, tmp_path)

    first = asyncio.run(tts.generate_speech("One"))
    second = asyncio.run(tts.generate_speech("Two"))

    assert first != second
