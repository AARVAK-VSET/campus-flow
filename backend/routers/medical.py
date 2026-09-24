from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from backend.database import get_db
from backend.models.medical import MedicalRecord
from backend.schemas import MedicalRecordCreate, MedicalRecordUpdate, MedicalRecordOut
from backend.services.analytics import get_medical_analytics
from backend.services.llm import get_medical_insights, parse_voice_command

router = APIRouter(prefix="/api/medical", tags=["Medical"])

@router.get("/", response_model=List[MedicalRecordOut])
def read_medical_records(
    skip: int = 0,
    limit: int = 100,
    student_name: Optional[str] = None,
    branch: Optional[str] = None,
    severity: Optional[str] = None,
    treatment_status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    limit = min(limit, 1000)
    query = db.query(MedicalRecord)
    if student_name:
        query = query.filter(MedicalRecord.student_name.ilike(f"%{student_name}%"))
    if branch:
        query = query.filter(MedicalRecord.branch == branch)
    if severity:
        query = query.filter(MedicalRecord.severity == severity)
    if treatment_status:
        query = query.filter(MedicalRecord.treatment_status == treatment_status)
        
    records = query.offset(skip).limit(limit).all()
    return records

@router.post("/", response_model=MedicalRecordOut)
def create_medical_record(record: MedicalRecordCreate, db: Session = Depends(get_db)):
    db_record = MedicalRecord(**record.dict())
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    return db_record

@router.put("/{record_id}", response_model=MedicalRecordOut)
def update_medical_record(record_id: int, record: MedicalRecordUpdate, db: Session = Depends(get_db)):
    db_record = db.query(MedicalRecord).filter(MedicalRecord.id == record_id).first()
    if not db_record:
        raise HTTPException(status_code=404, detail="Record not found")
    
    update_data = record.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_record, key, value)
    
    db.commit()
    db.refresh(db_record)
    return db_record

@router.delete("/{record_id}")
def delete_medical_record(record_id: int, db: Session = Depends(get_db)):
    db_record = db.query(MedicalRecord).filter(MedicalRecord.id == record_id).first()
    if not db_record:
        raise HTTPException(status_code=404, detail="Record not found")
    
    db.delete(db_record)
    db.commit()
    return {"message": "Record deleted"}

@router.get("/analytics")
async def get_medical_dashboard(db: Session = Depends(get_db)):
    stats = get_medical_analytics(db)
    insights = await get_medical_insights(stats)
    return {"stats": stats, "insights": insights}

@router.post("/voice")
async def process_medical_voice(command: str):
    return await parse_voice_command(command, "medical")

