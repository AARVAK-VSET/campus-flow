import importlib
from types import SimpleNamespace

import pytest
from sqlalchemy.engine import make_url

import backend.database as database


@pytest.fixture(autouse=True)
def restore_default_database(monkeypatch):
    yield
    monkeypatch.delenv("DATABASE_URL", raising=False)
    importlib.reload(database)


def test_database_url_defaults_to_local_sqlite(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    module = importlib.reload(database)

    assert module.SQLALCHEMY_DATABASE_URL == module.DEFAULT_DATABASE_URL
    assert module.engine.url.get_backend_name() == "sqlite"


def test_database_url_supports_custom_sqlite_path(monkeypatch, tmp_path):
    url = f"sqlite:///{tmp_path / 'custom.db'}"
    monkeypatch.setenv("DATABASE_URL", url)
    module = importlib.reload(database)

    assert module.SQLALCHEMY_DATABASE_URL == url
    assert module.engine.url == make_url(url)
    assert module.engine.url.get_backend_name() == "sqlite"


def test_database_url_supports_postgresql(monkeypatch):
    url = "postgresql://user:password@localhost/campus"
    monkeypatch.setenv("DATABASE_URL", url)

    # Use a stand-in for create_engine so this test does not need a PostgreSQL
    # driver (psycopg2) installed and never opens a connection.
    created = {}

    def fake_create_engine(engine_url, **kwargs):
        created["url"] = engine_url
        created["kwargs"] = kwargs
        return SimpleNamespace(url=make_url(engine_url))

    with monkeypatch.context() as patch:
        patch.setattr("sqlalchemy.create_engine", fake_create_engine)
        module = importlib.reload(database)

    assert module.SQLALCHEMY_DATABASE_URL == url
    assert created["url"] == url
    assert module.engine.url.get_backend_name() == "postgresql"
    # SQLite-only options must not be passed to other databases.
    assert "connect_args" not in created["kwargs"]
