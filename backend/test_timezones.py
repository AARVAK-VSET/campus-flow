from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import create_engine, text
from sqlalchemy.dialects import sqlite
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.schema import CreateTable

from backend.database import Base, get_db
from backend.main import app
from backend.models.announcement import Announcement
from backend.models.medical import MedicalRecord
from backend.models.parking import ParkingRecord
from backend.routers import medical
from backend.schemas import MedicalRecordOut
from backend.services import analytics
from backend.services.analytics import get_medical_analytics
from backend.timeutils import as_utc, utcnow

UTC = timezone.utc
IST = timezone(timedelta(hours=5, minutes=30))
NOW = datetime(2026, 9, 20, 12, 0, tzinfo=UTC)


def _record(when, issue="Fever"):
    return MedicalRecord(student_name="A", branch="CSE", year=1, issue=issue, severity="low", date_time=when)


class _StubSession:
    """Hands analytics records with exactly the datetimes given.

    A real SQLite session returns naive datetimes, which would hide the naive/aware mix.
    """

    def __init__(self, records):
        self._records = records

    def query(self, model):
        return self

    def all(self):
        return self._records


def _visits_by_day(records):
    result = get_medical_analytics(_StubSession(records))
    return {row["date"]: row["count"] for row in result["daily_visits"]}


@pytest.fixture
def fixed_now(monkeypatch):
    monkeypatch.setattr(analytics, "utcnow", lambda: NOW)


@pytest.fixture
def engine():
    eng = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=eng)
    yield eng
    eng.dispose()


def _session(engine):
    return sessionmaker(bind=engine, autoflush=False)()


@pytest.fixture
def client(engine):
    make_session = sessionmaker(bind=engine, autoflush=False)

    def override_get_db():
        session = make_session()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


# ---- Helpers ----

def test_utcnow_is_aware_utc():
    assert utcnow().utcoffset() == timedelta(0)


def test_as_utc_treats_naive_as_utc():
    assert as_utc(datetime(2026, 9, 20, 10, 0)) == datetime(2026, 9, 20, 10, 0, tzinfo=UTC)


def test_as_utc_converts_aware_instead_of_dropping_the_offset():
    converted = as_utc(datetime(2026, 9, 20, 10, 0, tzinfo=IST))
    assert converted == datetime(2026, 9, 20, 4, 30, tzinfo=UTC)
    assert converted.utcoffset() == timedelta(0)


# ---- Medical analytics comparisons ----

def test_analytics_handles_mixed_naive_and_aware_timestamps(fixed_now):
    records = [
        _record(datetime(2026, 9, 19, 8, 0)),  # naive, taken as UTC
        _record(datetime(2026, 9, 19, 9, 0, tzinfo=UTC)),  # aware UTC
        _record(datetime(2026, 9, 19, 14, 30, tzinfo=IST)),  # aware, 09:00 UTC
        _record(None),  # no timestamp: counted in the total, not in the visits
    ]
    result = get_medical_analytics(_StubSession(records))
    assert result["total"] == 4
    assert {row["date"]: row["count"] for row in result["daily_visits"]} == {"2026-09-19": 3}


def test_recent_window_is_the_last_30_days_inclusive(fixed_now):
    edge = NOW - timedelta(days=30)
    just_outside = edge - timedelta(seconds=1)
    records = [
        _record(edge),
        _record(edge.replace(tzinfo=None)),
        _record(just_outside),
        _record(just_outside.replace(tzinfo=None)),
    ]
    assert _visits_by_day(records) == {"2026-08-21": 2}


def test_offsets_are_converted_not_dropped_at_the_window_edge(fixed_now):
    # The window starts 2026-08-21 12:00 UTC.
    west = timezone(timedelta(hours=-8))
    inside = _record(datetime(2026, 8, 21, 5, 0, tzinfo=west))  # 13:00 UTC; without the offset it reads 05:00
    outside = _record(datetime(2026, 8, 21, 13, 30, tzinfo=IST))  # 08:00 UTC; without the offset it reads 13:30
    assert _visits_by_day([inside, outside]) == {"2026-08-21": 1}


def test_daily_visits_are_bucketed_by_utc_date(fixed_now):
    # 23:30 on the 19th at UTC-5 is 04:30 on the 20th in UTC.
    late_evening = _record(datetime(2026, 9, 19, 23, 30, tzinfo=timezone(timedelta(hours=-5))))
    assert _visits_by_day([late_evening]) == {"2026-09-20": 1}


def test_medical_analytics_endpoint_counts_recent_visits(client, engine, monkeypatch):
    async def fake_insights(stats):
        return "ok"

    monkeypatch.setattr(medical, "get_medical_insights", fake_insights)
    with _session(engine) as s:
        s.add_all(
            [
                _record(utcnow() - timedelta(days=1)),
                _record(datetime.now(IST) - timedelta(days=2)),
                _record(utcnow() - timedelta(days=60)),
            ]
        )
        s.commit()

    response = client.get("/api/medical/analytics")
    assert response.status_code == 200
    stats = response.json()["stats"]
    assert stats["total"] == 3
    assert sum(row["count"] for row in stats["daily_visits"]) == 2


# ---- Timezone-aware model columns ----

def test_aware_input_is_stored_as_utc_and_read_back_aware(engine):
    ist_ten = datetime(2026, 9, 20, 10, 0, tzinfo=IST)  # 04:30 UTC
    with _session(engine) as s:
        s.add(_record(ist_ten))
        s.commit()
    with engine.connect() as conn:
        raw = conn.execute(text("select date_time from medical_records")).scalar()
    assert raw == "2026-09-20 04:30:00.000000"  # UTC wall clock, in the existing storage format
    with _session(engine) as s:
        stored = s.query(MedicalRecord).one().date_time
    assert stored == ist_ten
    assert stored.utcoffset() == timedelta(0)


def test_naive_input_is_treated_as_utc(engine):
    with _session(engine) as s:
        s.add(_record(datetime(2026, 9, 20, 10, 0)))
        s.commit()
    with _session(engine) as s:
        assert s.query(MedicalRecord).one().date_time == datetime(2026, 9, 20, 10, 0, tzinfo=UTC)


def test_legacy_naive_rows_are_read_as_utc(engine):
    with engine.begin() as conn:
        conn.execute(
            text(
                "insert into medical_records (student_name, branch, year, issue, date_time) "
                "values ('A', 'CSE', 1, 'Fever', '2026-09-20 10:00:00.000000')"
            )
        )
    with _session(engine) as s:
        assert s.query(MedicalRecord).one().date_time == datetime(2026, 9, 20, 10, 0, tzinfo=UTC)


def test_default_timestamps_are_aware_utc(engine):
    before = utcnow() - timedelta(seconds=1)
    with _session(engine) as s:
        s.add_all(
            [
                MedicalRecord(student_name="A", branch="CSE", year=1, issue="Fever"),
                ParkingRecord(car_number="X", slot_number=1),
                Announcement(message="hi"),
            ]
        )
        s.commit()
    after = utcnow() + timedelta(seconds=1)
    with _session(engine) as s:
        parking = s.query(ParkingRecord).one()
        stamps = [s.query(MedicalRecord).one().date_time, parking.time_in, s.query(Announcement).one().created_at]
    for stamp in stamps:
        assert stamp.utcoffset() == timedelta(0)
        assert before <= stamp <= after
    assert parking.time_out is None


@pytest.mark.parametrize(
    "model,columns",
    [(MedicalRecord, ["date_time"]), (ParkingRecord, ["time_in", "time_out"]), (Announcement, ["created_at"])],
)
def test_sqlite_column_type_is_unchanged(model, columns):
    ddl = str(CreateTable(model.__table__).compile(dialect=sqlite.dialect()))
    for column in columns:
        assert f"{column} DATETIME" in ddl


# ---- Timezone-aware API boundary ----

def test_response_schema_rejects_naive_timestamps():
    payload = dict(id=1, student_name="A", branch="CSE", year=1, issue="Fever")
    with pytest.raises(ValidationError):
        MedicalRecordOut(**payload, date_time=datetime(2026, 9, 20, 10, 0))
    assert MedicalRecordOut(**payload, date_time=NOW).date_time == NOW


def test_medical_list_returns_timestamps_with_a_utc_offset(client, engine):
    with _session(engine) as s:
        s.add(_record(datetime(2026, 9, 20, 10, 0)))
        s.commit()
    response = client.get("/api/medical/")
    assert response.status_code == 200
    assert response.json()[0]["date_time"].endswith(("Z", "+00:00"))


def _create_parking(client):
    response = client.post("/api/parking/", json={"car_number": "MH12AB1234", "slot_number": 1})
    assert response.status_code == 200
    return response.json()


def test_parking_response_timestamps_carry_a_utc_offset(client):
    assert _create_parking(client)["time_in"].endswith(("Z", "+00:00"))


def test_parking_time_out_rejects_naive_datetime(client):
    parking_id = _create_parking(client)["id"]
    response = client.put(f"/api/parking/{parking_id}", json={"time_out": "2026-09-20T10:00:00"})
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", "time_out"]


def test_parking_time_out_is_converted_to_utc(client):
    parking_id = _create_parking(client)["id"]
    response = client.put(
        f"/api/parking/{parking_id}", json={"status": "free", "time_out": "2026-09-20T10:00:00+05:30"}
    )
    assert response.status_code == 200
    assert response.json()["time_out"] in ("2026-09-20T04:30:00Z", "2026-09-20T04:30:00+00:00")


def test_parking_time_out_accepts_the_frontend_iso_string(client):
    # Parking.tsx sends new Date().toISOString()
    parking_id = _create_parking(client)["id"]
    response = client.put(f"/api/parking/{parking_id}", json={"time_out": "2026-09-20T10:00:00.123Z"})
    assert response.status_code == 200
