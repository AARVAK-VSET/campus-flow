import os
import time

from backend.services import tts
import backend.routers.voice as voice


def test_audio_response_sweeps_expired_cache_without_deleting_served_file(client, monkeypatch, tmp_path):
    audio_dir = tmp_path / "audio_cache"
    audio_dir.mkdir()
    monkeypatch.setattr(voice, "AUDIO_DIR", str(audio_dir))
    monkeypatch.setattr(tts, "AUDIO_DIR", str(audio_dir))

    served_file = audio_dir / "served.mp3"
    served_file.write_bytes(b"fake-mp3-bytes")

    expired_file = audio_dir / "expired.mp3"
    expired_file.write_bytes(b"old")
    expired_time = time.time() - tts.AUDIO_CACHE_TTL - 1
    os.utime(expired_file, (expired_time, expired_time))

    response = client.get("/api/voice/audio/served.mp3")

    assert response.status_code == 200
    assert response.content == b"fake-mp3-bytes"

    # The background task runs after the response is sent: expired cache
    # entries are swept, but the file that was just served is left alone
    # so an identical next request can still reuse it.
    assert not expired_file.exists()
    assert served_file.exists()


def test_audio_endpoint_404s_for_a_missing_file(client, monkeypatch, tmp_path):
    audio_dir = tmp_path / "audio_cache"
    audio_dir.mkdir()
    monkeypatch.setattr(voice, "AUDIO_DIR", str(audio_dir))

    response = client.get("/api/voice/audio/does-not-exist.mp3")

    assert response.status_code == 404
