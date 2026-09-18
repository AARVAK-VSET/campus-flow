from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from backend.database import get_db
from backend.models.parking import ParkingRecord
from backend.schemas import ParkingRecordCreate, ParkingRecordUpdate, ParkingRecordOut
from backend.services.analytics import get_parking_analytics
from backend.services.llm import get_parking_insights
from datetime import datetime

router = APIRouter(prefix="/api/parking", tags=["Parking"])

@router.get("/", response_model=List[ParkingRecordOut])
def read_parking_records(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    records = db.query(ParkingRecord).offset(skip).limit(limit).all()
    return records

@router.post("/", response_model=ParkingRecordOut)
def create_parking_record(record: ParkingRecordCreate, db: Session = Depends(get_db)):
    db_record = ParkingRecord(**record.dict())
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    return db_record

@router.put("/{record_id}", response_model=ParkingRecordOut)
def update_parking_record(record_id: int, record: ParkingRecordUpdate, db: Session = Depends(get_db)):
    db_record = db.query(ParkingRecord).filter(ParkingRecord.id == record_id).first()
    if not db_record:
        raise HTTPException(status_code=404, detail="Record not found")
    
    update_data = record.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_record, key, value)
    
    db.commit()
    db.refresh(db_record)
    return db_record

@router.get("/analytics")
async def get_parking_dashboard(db: Session = Depends(get_db)):
    stats = get_parking_analytics(db)
    insights = await get_parking_insights(stats)
    return {"stats": stats, "insights": insights}

@router.post("/detect")
async def detect_parking_slots(image: UploadFile = File(...)):
    # Simulated CV detection for 10 slots
    import random
    
    prefixes = ["MH12", "DL04", "KA01", "TN07", "HR26"]
    
    slots = []
    for i in range(1, 11):
        is_occupied = random.choice([True, False])
        car_num = f"{random.choice(prefixes)}-{chr(random.randint(65, 90))}{chr(random.randint(65, 90))}-{random.randint(1000, 9999)}" if is_occupied else None
        slots.append({
            "id": i,
            "status": "occupied" if is_occupied else "free",
            "car_number": car_num
        })
    
    return {"slots": slots, "processing_time": "0.8s", "confidence": 0.94}

