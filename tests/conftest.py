"""Shared pytest fixtures for the CampusFlow backend.

Every test runs against a throw-away, in-memory SQLite database:

* nothing is ever written to disk (no campus.db, no audio files);
* every change a test makes is rolled back when the test ends, so tests
  cannot affect each other;
* the AI (OpenRouter) and text-to-speech (edge-tts) services are replaced with
  fakes, so the suite needs no internet connection and no API keys.
"""
import os

# Point the app at an in-memory database BEFORE any backend module is imported:
# backend.database reads DATABASE_URL when it is first imported. Forcing the value
# (instead of using setdefault) also guarantees a developer's real DATABASE_URL is
# never touched by the tests.
os.environ["DATABASE_URL"] = "sqlite://"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import edge_tts

from backend.database import Base, get_db
from backend.main import app
from backend.services import llm

FAKE_INSIGHT = "FAKE AI INSIGHT"


@pytest.fixture(scope="session")
def engine():
    """One in-memory database for the whole test session (tables created once)."""
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        # StaticPool keeps a single shared connection, so the web app's worker
        # threads and the test itself all see the same in-memory database.
        poolclass=StaticPool,
    )

    # Documented SQLAlchemy recipe: the built-in sqlite driver does not start
    # transactions properly, which breaks the SAVEPOINTs used for test rollback.
    @event.listens_for(test_engine, "connect")
    def _do_connect(dbapi_connection, connection_record):
        dbapi_connection.isolation_level = None

    @event.listens_for(test_engine, "begin")
    def _do_begin(conn):
        conn.exec_driver_sql("BEGIN")

    Base.metadata.create_all(bind=test_engine)
    yield test_engine
    test_engine.dispose()


@pytest.fixture()
def db_session(engine):
    """A database session whose changes are rolled back after every test."""
    connection = engine.connect()
    outer_transaction = connection.begin()
    session = sessionmaker(
        bind=connection,
        autoflush=False,
        autocommit=False,
        # session.commit() (also inside the API routes) only releases a SAVEPOINT;
        # the outer transaction is what we roll back at the end of the test.
        join_transaction_mode="create_savepoint",
    )()
    try:
        yield session
    finally:
        session.close()
        outer_transaction.rollback()
        connection.close()


@pytest.fixture()
def client(db_session):
    """FastAPI test client that uses the rolled-back test session."""

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    # Deliberately NOT `with TestClient(app)`: that would run the app's startup
    # code, which creates the real database file and audio folder.
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def fake_llm(monkeypatch):
    """No test may call the real AI service, even if an API key is configured."""

    async def fake_ask_llm(system_prompt, user_prompt):
        return FAKE_INSIGHT

    monkeypatch.setattr(llm, "_ask_llm", fake_ask_llm)


@pytest.fixture(autouse=True)
def block_real_speech(monkeypatch):
    """No test may call the real text-to-speech service (it needs the internet)."""

    class BlockedCommunicate:
        def __init__(self, *args, **kwargs):
            raise RuntimeError("Real edge-tts calls are blocked in tests; use a fake.")

    monkeypatch.setattr(edge_tts, "Communicate", BlockedCommunicate)


@pytest.fixture()
def fake_insight():
    """The text returned by the fake AI service, for assertions."""
    return FAKE_INSIGHT
