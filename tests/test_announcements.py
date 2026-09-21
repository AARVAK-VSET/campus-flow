import edge_tts
import pytest

from backend.services.tts import VOICE_MAP

ANNOUNCEMENT = {"message": "Library closes at 8 PM", "language": "en"}


class FakeCommunicate:
    """Stand-in for edge_tts.Communicate: streams two audio chunks, no network."""

    created = []

    def __init__(self, text, voice):
        FakeCommunicate.created.append((text, voice))

    async def stream(self):
        yield {"type": "audio", "data": b"abc"}
        yield {"type": "WordBoundary", "offset": 0}
        yield {"type": "audio", "data": b"def"}


@pytest.fixture()
def fake_speech(monkeypatch):
    FakeCommunicate.created = []
    monkeypatch.setattr(edge_tts, "Communicate", FakeCommunicate)
    return FakeCommunicate


def _create(client, **overrides):
    response = client.post("/api/announcements/", json={**ANNOUNCEMENT, **overrides})
    assert response.status_code == 200, response.text
    return response.json()


def test_create_announcement_applies_defaults(client):
    body = _create(client, language="hi")

    assert body["id"] > 0
    assert body["language"] == "hi"
    assert body["repeat_interval"] == 0
    assert body["is_active"] is True


def test_create_rejects_missing_message(client):
    assert client.post("/api/announcements/", json={"language": "en"}).status_code == 422


def test_list_and_delete_announcements(client):
    first = _create(client, message="One")
    _create(client, message="Two")

    assert [a["message"] for a in client.get("/api/announcements/").json()] == ["One", "Two"]

    assert client.delete(f"/api/announcements/{first['id']}").status_code == 200
    assert [a["message"] for a in client.get("/api/announcements/").json()] == ["Two"]


def test_delete_missing_announcement_returns_404(client):
    assert client.delete("/api/announcements/999").status_code == 404


def test_speak_streams_audio_using_the_announcement_language(client, fake_speech):
    announcement = _create(client, language="hi")

    response = client.post(f"/api/announcements/{announcement['id']}/speak")

    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/mpeg"
    assert response.content == b"abcdef"
    assert fake_speech.created == [("Library closes at 8 PM", VOICE_MAP["hi"])]


def test_speak_language_query_overrides_the_saved_language(client, fake_speech):
    announcement = _create(client, language="en")

    client.post(f"/api/announcements/{announcement['id']}/speak?language=fr")

    assert fake_speech.created[0][1] == VOICE_MAP["fr"]


def test_speak_unsupported_language_returns_400(client, fake_speech):
    announcement = _create(client, language="xx")

    response = client.post(f"/api/announcements/{announcement['id']}/speak")

    assert response.status_code == 400
    assert "Unsupported language" in response.json()["detail"]
    assert fake_speech.created == []


def test_speak_missing_announcement_returns_404(client, fake_speech):
    assert client.post("/api/announcements/999/speak").status_code == 404


def test_speak_returns_502_when_no_audio_is_produced(client, monkeypatch):
    class SilentCommunicate:
        def __init__(self, text, voice):
            pass

        async def stream(self):
            yield {"type": "WordBoundary", "offset": 0}

    monkeypatch.setattr(edge_tts, "Communicate", SilentCommunicate)
    announcement = _create(client)

    response = client.post(f"/api/announcements/{announcement['id']}/speak")

    assert response.status_code == 502
    assert "no audio" in response.json()["detail"]


def test_speak_returns_502_when_synthesis_fails(client, monkeypatch):
    class BrokenCommunicate:
        def __init__(self, text, voice):
            pass

        async def stream(self):
            raise RuntimeError("service down")
            yield  # pragma: no cover - makes this an async generator

    monkeypatch.setattr(edge_tts, "Communicate", BrokenCommunicate)
    announcement = _create(client)

    response = client.post(f"/api/announcements/{announcement['id']}/speak")

    assert response.status_code == 502
    assert "service down" in response.json()["detail"]
