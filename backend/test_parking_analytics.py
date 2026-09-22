from datetime import datetime

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.database import Base, get_db
from backend.models.parking import ParkingRecord
from backend.routers import parking
from backend.services.analytics import _parse_timestamp, get_parking_analytics


def make_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    return engine, sessionmaker(autocommit=False, autoflush=False, bind=engine)


def insert_raw_records(engine, rows):
    # Raw SQL so corrupt values bypass SQLAlchemy's DateTime type, as with legacy data
    with engine.begin() as conn:
        for car_number, slot_number, time_in, status in rows:
            conn.execute(
                text(
                    "INSERT INTO parking_records (car_number, slot_number, time_in, status) "
                    "VALUES (:car_number, :slot_number, :time_in, :status)"
                ),
                {"car_number": car_number, "slot_number": slot_number, "time_in": time_in, "status": status},
            )


CORRUPT_ROWS = [
    ("MH12-AB-1234", 1, "2026-01-05 09:15:00", "occupied"),
    ("DL04-CD-5678", 2, "2026-01-05 09:45:30.123456", "free"),
    ("KA01-EF-9012", 3, "2026-01-05 14:00:00", "occupied"),
    ("TN07-GH-3456", 4, None, "occupied"),
    ("HR26-IJ-7890", 5, "not-a-timestamp", "free"),
    ("MH12-KL-1111", 5, "", "free"),
    ("DL04-MN-2222", 6, 12345, "occupied"),
]


def test_parse_timestamp_handles_null_and_non_datetime_values():
    now = datetime(2026, 1, 5, 9, 15)

    assert _parse_timestamp(now) is now
    assert _parse_timestamp("2026-01-05 09:15:00") == now
    assert _parse_timestamp("2026-01-05T09:15:00") == now
    assert _parse_timestamp(None) is None
    assert _parse_timestamp("") is None
    assert _parse_timestamp("garbage") is None
    assert _parse_timestamp(12345) is None


def test_parking_analytics_skips_null_and_corrupt_timestamps():
    engine, SessionLocal = make_session()
    insert_raw_records(engine, CORRUPT_ROWS)

    db = SessionLocal()
    try:
        stats = get_parking_analytics(db)
    finally:
        db.close()

    assert stats["total"] == 7
    assert stats["occupied"] == 4
    assert stats["free"] == 3
    assert stats["hourly"] == [{"hour": 9, "count": 2}, {"hour": 14, "count": 1}]
    assert stats["slot_usage"] == [
        {"slot": 1, "count": 1},
        {"slot": 2, "count": 1},
        {"slot": 3, "count": 1},
        {"slot": 4, "count": 1},
        {"slot": 5, "count": 2},
        {"slot": 6, "count": 1},
    ]


def test_parking_analytics_with_valid_orm_records():
    engine, SessionLocal = make_session()

    db = SessionLocal()
    try:
        db.add_all([
            ParkingRecord(car_number="MH12-AB-1234", slot_number=1, time_in=datetime(2026, 1, 5, 8, 0)),
            ParkingRecord(car_number="DL04-CD-5678", slot_number=1, time_in=datetime(2026, 1, 5, 8, 30), status="free"),
        ])
        db.commit()
        stats = get_parking_analytics(db)
    finally:
        db.close()

    assert stats["total"] == 2
    assert stats["occupied"] == 1
    assert stats["free"] == 1
    assert stats["hourly"] == [{"hour": 8, "count": 2}]
    assert stats["slot_usage"] == [{"slot": 1, "count": 2}]


def test_parking_analytics_empty():
    _, SessionLocal = make_session()

    db = SessionLocal()
    try:
        stats = get_parking_analytics(db)
    finally:
        db.close()

    assert stats == {"total": 0, "occupied": 0, "free": 0, "hourly": [], "slot_usage": []}


def test_parking_analytics_endpoint_returns_200_with_corrupt_records(monkeypatch):
    engine, SessionLocal = make_session()
    insert_raw_records(engine, CORRUPT_ROWS)

    async def fake_insights(stats):
        return "insights"

    monkeypatch.setattr(parking, "get_parking_insights", fake_insights)

    def override_get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    app = FastAPI()
    app.include_router(parking.router)
    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)

    response = client.get("/api/parking/analytics")

    assert response.status_code == 200
    body = response.json()
    assert body["insights"] == "insights"
    assert body["stats"]["total"] == 7
    assert body["stats"]["hourly"] == [{"hour": 9, "count": 2}, {"hour": 14, "count": 1}]
