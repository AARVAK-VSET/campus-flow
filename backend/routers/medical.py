from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
import time
import httpx

from backend.database import get_db
from backend.models.medical import MedicalRecord
from backend.schemas import MedicalRecordCreate, MedicalRecordUpdate, MedicalRecordOut
from backend.services.analytics import get_medical_analytics
from backend.services.llm import get_medical_insights, parse_voice_command


router = APIRouter(prefix="/api/medical", tags=["Medical"])


# Simple in-memory cache for geocoding results.
# Key: normalized address
# Value: (timestamp, coordinates)
GEOCODE_CACHE = {}
GEOCODE_CACHE_TTL = 24 * 60 * 60  # 24 hours


@router.get("/geocode")
async def geocode_address(address: str = Query(..., min_length=1)):
    """Proxy address geocoding through the backend."""

    cache_key = address.strip().lower()

    # Check cache first
    cached = GEOCODE_CACHE.get(cache_key)

    if cached:
        cached_at, coordinates = cached

        if time.time() - cached_at < GEOCODE_CACHE_TTL:
            return coordinates

        # Remove expired cache entry
        del GEOCODE_CACHE[cache_key]

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                "https://nominatim.openstreetmap.org/search",
                params={
                    "format": "json",
                    "q": address,
                    "limit": 1,
                },
                headers={
                    "User-Agent": "CampusFlow/1.0 (CampusFlow application)",
                },
            )

            response.raise_for_status()

        data = response.json()

        if not data:
            raise HTTPException(
                status_code=404,
                detail="Address could not be geocoded.",
            )

        coordinates = {
            "lat": float(data[0]["lat"]),
            "lon": float(data[0]["lon"]),
        }

        # Store successful result in cache
        GEOCODE_CACHE[cache_key] = (time.time(), coordinates)

        return coordinates

    except HTTPException:
        raise

    except (httpx.HTTPError, ValueError, KeyError) as exc:
        print(f"Geocoding request failed: {exc}")

        raise HTTPException(
            status_code=502,
            detail="Geocoding service is temporarily unavailable.",
        )


@router.get("/", response_model=List[MedicalRecordOut])
def read_medical_records(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    records = db.query(MedicalRecord).offset(skip).limit(limit).all()
    return records


@router.post("/", response_model=MedicalRecordOut)
def create_medical_record(
    record: MedicalRecordCreate,
    db: Session = Depends(get_db),
):
    print(f"DEBUG: Received record: {record.dict()}")
    db_record = MedicalRecord(**record.dict())
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    return db_record


@router.put("/{record_id}", response_model=MedicalRecordOut)
def update_medical_record(
    record_id: int,
    record: MedicalRecordUpdate,
    db: Session = Depends(get_db),
):
    db_record = (
        db.query(MedicalRecord)
        .filter(MedicalRecord.id == record_id)
        .first()
    )

    if not db_record:
        raise HTTPException(status_code=404, detail="Record not found")

    update_data = record.dict(exclude_unset=True)

    for key, value in update_data.items():
        setattr(db_record, key, value)

    db.commit()
    db.refresh(db_record)
    return db_record


@router.delete("/{record_id}")
def delete_medical_record(
    record_id: int,
    db: Session = Depends(get_db),
):
    db_record = (
        db.query(MedicalRecord)
        .filter(MedicalRecord.id == record_id)
        .first()
    )

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
