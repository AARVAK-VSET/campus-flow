import pytest
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.main import app
from backend.database import get_db, SessionLocal
from backend.models.parking import ParkingRecord
from fastapi.testclient import TestClient

router = APIRouter()

@router.post("/api/test_rollback_trigger")
def trigger_rollback(db: Session = Depends(get_db)):
    # 1. Mutate the database
    record = ParkingRecord(car_number="ROLLBACK_TEST", slot_number=999, status="occupied")
    db.add(record)
    db.flush() # flush to ensure it's in the transaction
    
    # 2. Raise an exception mid-transaction
    raise HTTPException(status_code=500, detail="Simulated error")

app.include_router(router)

client = TestClient(app)

def test_rollback_on_error():
    db = SessionLocal()
    # Ensure starting clean
    db.query(ParkingRecord).filter(ParkingRecord.car_number == "ROLLBACK_TEST").delete()
    db.commit()
    
    response = client.post("/api/test_rollback_trigger")
    assert response.status_code == 500
    
    # Verify the partial mutation is not in the database
    count = db.query(ParkingRecord).filter(ParkingRecord.car_number == "ROLLBACK_TEST").count()
    assert count == 0
    
    db.close()
