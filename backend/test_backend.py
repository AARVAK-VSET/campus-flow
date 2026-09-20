import os
import sys
from datetime import datetime
import pytest
from fastapi.testclient import TestClient

# Ensure repo root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from backend.main import app
    from backend.database import SessionLocal, init_db
    from backend.models.parking import ParkingRecord
except ImportError:
    from main import app
    from database import SessionLocal, init_db
    from models.parking import ParkingRecord

init_db()
client = TestClient(app)


@pytest.fixture(autouse=True)
def cleanup_parking_records():
    """Ensure a clean parking table before each test."""
    db = SessionLocal()
    try:
        db.query(ParkingRecord).delete()
        db.commit()
    finally:
        db.close()
    yield
    db = SessionLocal()
    try:
        db.query(ParkingRecord).delete()
        db.commit()
    finally:
        db.close()


def test_parking_filters_and_checkout():
    """
    Test Step 4 requirements:
    - Create three records: two active and one checked out.
    - status=active returns exactly the two active ones.
    - car_number=... returns only that vehicle.
    - After a vehicle checks out, it disappears from the active results.
    """
    db = SessionLocal()
    try:
        # Create two active records
        rec1 = ParkingRecord(
            car_number="DL01AB1234",
            slot_number=1,
            status="occupied",
            time_in=datetime.utcnow(),
            time_out=None,
        )
        rec2 = ParkingRecord(
            car_number="MH12CD5678",
            slot_number=2,
            status="occupied",
            time_in=datetime.utcnow(),
            time_out=None,
        )
        # Create one checked-out record
        rec3 = ParkingRecord(
            car_number="KA01EF9012",
            slot_number=3,
            status="free",
            time_in=datetime.utcnow(),
            time_out=datetime.utcnow(),
        )
        db.add_all([rec1, rec2, rec3])
        db.commit()
        db.refresh(rec1)
        db.refresh(rec2)
        db.refresh(rec3)
        rec1_id = rec1.id
        rec2_id = rec2.id
    finally:
        db.close()

    # 1. status=active returns exactly the two active ones
    res = client.get("/api/parking/?status=active")
    assert res.status_code == 200, res.text
    active_data = res.json()
    assert len(active_data) == 2
    active_car_numbers = {r["car_number"] for r in active_data}
    assert active_car_numbers == {"DL01AB1234", "MH12CD5678"}

    # 2. car_number=... returns only that vehicle
    res_car = client.get("/api/parking/?car_number=DL01AB1234")
    assert res_car.status_code == 200, res_car.text
    car_data = res_car.json()
    assert len(car_data) == 1
    assert car_data[0]["car_number"] == "DL01AB1234"

    # 3. slot_number=... returns only that slot
    res_slot = client.get("/api/parking/?slot_number=2")
    assert res_slot.status_code == 200, res_slot.text
    slot_data = res_slot.json()
    assert len(slot_data) == 1
    assert slot_data[0]["slot_number"] == 2

    # 4. Filters combine: status=active & slot_number=1
    res_combined = client.get("/api/parking/?status=active&slot_number=1")
    assert res_combined.status_code == 200
    combined_data = res_combined.json()
    assert len(combined_data) == 1
    assert combined_data[0]["car_number"] == "DL01AB1234"

    # 5. After a vehicle checks out, it disappears from the active results
    checkout_res = client.put(
        f"/api/parking/{rec1_id}",
        json={"status": "free", "time_out": datetime.utcnow().isoformat()},
    )
    assert checkout_res.status_code == 200

    # Query status=active again
    res_after = client.get("/api/parking/?status=active")
    assert res_after.status_code == 200
    after_data = res_after.json()
    assert len(after_data) == 1
    assert after_data[0]["id"] == rec2_id
    assert after_data[0]["car_number"] == "MH12CD5678"


def test_parking_invalid_status_returns_400():
    """Ensure invalid status query param returns a clear 400 error."""
    res = client.get("/api/parking/?status=unknown_status_xyz")
    assert res.status_code == 400
    assert "Invalid status" in res.json().get("detail", "")


def test_parking_records_endpoint_alias():
    """Ensure /records route alias works with status filtering."""
    db = SessionLocal()
    try:
        rec = ParkingRecord(
            car_number="UP16AA0001",
            slot_number=5,
            status="occupied",
            time_in=datetime.utcnow(),
            time_out=None,
        )
        db.add(rec)
        db.commit()
    finally:
        db.close()

    res = client.get("/api/parking/records?status=active")
    assert res.status_code == 200
    records = res.json()
    assert len(records) == 1
    assert records[0]["car_number"] == "UP16AA0001"


def test_parking_no_filters_preserves_all():
    """Ensure omitting filters returns all records (unfiltered behavior)."""
    db = SessionLocal()
    try:
        rec1 = ParkingRecord(
            car_number="CAR1", slot_number=1, status="occupied", time_in=datetime.utcnow()
        )
        rec2 = ParkingRecord(
            car_number="CAR2", slot_number=2, status="free", time_in=datetime.utcnow(), time_out=datetime.utcnow()
        )
        db.add_all([rec1, rec2])
        db.commit()
    finally:
        db.close()

    res = client.get("/api/parking/")
    assert res.status_code == 200
    records = res.json()
    assert len(records) == 2


if __name__ == "__main__":
    pytest.main(["-v", __file__])

