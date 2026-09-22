import os
import subprocess
import sys
from pathlib import Path

from fastapi.testclient import TestClient

import backend.main as main_module
from backend.main import app
from backend.services.llm import AIServiceTimeoutError

REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = REPO_ROOT / "backend"


def _listing(path: Path):
    return sorted(p.name for p in path.iterdir() if p.name != "__pycache__")


def test_health_check(client):
    response = client.get("/api/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "timestamp" in body


def test_root_returns_welcome_message(client):
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["status"] == "active"


def test_importing_the_app_creates_no_files(tmp_path):
    """Importing backend.main must not create the database file or audio folder."""
    probe_db = tmp_path / "probe.db"
    env = {
        **os.environ,
        "DATABASE_URL": f"sqlite:///{probe_db}",
        "PYTHONDONTWRITEBYTECODE": "1",
    }
    before = _listing(BACKEND_DIR)

    subprocess.run(
        [sys.executable, "-c", "import backend.main"],
        cwd=REPO_ROOT,
        env=env,
        check=True,
        capture_output=True,
        timeout=120,
    )

    assert not probe_db.exists()
    assert _listing(BACKEND_DIR) == before


def test_startup_initialises_database_and_audio_folder(monkeypatch, tmp_path):
    """The work removed from import time still happens when the server starts."""
    calls = []
    audio_dir = tmp_path / "audio_cache"
    monkeypatch.setattr(main_module, "init_db", lambda: calls.append("init_db"))
    monkeypatch.setattr(main_module, "AUDIO_DIR", str(audio_dir))

    with TestClient(app):  # entering the block runs the startup code
        assert calls == ["init_db"]
        assert audio_dir.is_dir()


def test_ai_service_timeout_returns_504(client, monkeypatch):
    async def fake_form_filler(current_data, user_input, context):
        raise AIServiceTimeoutError(
            "External AI service timed out after 30 seconds."
        )

    monkeypatch.setattr(
        main_module.voice,
        "conversational_form_filler",
        fake_form_filler,
    )

    response = client.post(
        "/api/voice/process",
        json={
            "user_input": "I have a fever",
            "current_data": {},
            "context": "medical",
        },
    )

    assert response.status_code == 504
    assert response.json() == {
        "detail": "External AI service timed out after 30 seconds."
    }
