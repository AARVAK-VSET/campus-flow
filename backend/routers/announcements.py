from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from backend.database import get_db
from backend.models.announcement import Announcement
from backend.schemas import AnnouncementCreate, AnnouncementOut
from backend.services.tts import generate_speech
from fastapi.responses import FileResponse

router = APIRouter(prefix="/api/announcements", tags=["Announcements"])

@router.get("/", response_model=List[AnnouncementOut])
def read_announcements(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    announcements = db.query(Announcement).offset(skip).limit(limit).all()
    return announcements

@router.post("/", response_model=AnnouncementOut)
def create_announcement(announcement: AnnouncementCreate, db: Session = Depends(get_db)):
    db_announcement = Announcement(**announcement.dict())
    db.add(db_announcement)
    db.commit()
    db.refresh(db_announcement)
    return db_announcement

@router.delete("/{announcement_id}")
def delete_announcement(announcement_id: int, db: Session = Depends(get_db)):
    db_announcement = db.query(Announcement).filter(Announcement.id == announcement_id).first()
    if not db_announcement:
        raise HTTPException(status_code=404, detail="Announcement not found")
    
    db.delete(db_announcement)
    db.commit()
    return {"message": "Announcement deleted"}

@router.post("/{announcement_id}/speak")
async def speak_announcement(announcement_id: int, db: Session = Depends(get_db)):
    db_announcement = db.query(Announcement).filter(Announcement.id == announcement_id).first()
    if not db_announcement:
        raise HTTPException(status_code=404, detail="Announcement not found")
    
    audio_path = await generate_speech(db_announcement.message, db_announcement.language)
    return FileResponse(audio_path, media_type="audio/mpeg")

