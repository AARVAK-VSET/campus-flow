from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import edge_tts
from backend.database import get_db
from backend.models.announcement import Announcement
from backend.schemas import AnnouncementCreate, AnnouncementOut
from backend.services.scheduler import scheduler, scheduler_lifespan
from backend.services.tts import VOICE_MAP

# The lifespan starts the recurring-announcement scheduler with the app and stops it on shutdown.
router = APIRouter(prefix="/api/announcements", tags=["Announcements"], lifespan=scheduler_lifespan)


async def _audio_only(communicate: edge_tts.Communicate):
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            yield chunk["data"]


@router.get("/", response_model=List[AnnouncementOut])
def read_announcements(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    announcements = db.query(Announcement).offset(skip).limit(limit).all()
    return announcements


@router.get("/broadcasts")
def read_recent_broadcasts(limit: int = Query(20, ge=1, le=100)):
    """Most recent scheduled broadcasts of recurring announcements, newest first."""
    recent = list(scheduler.history)[-limit:]
    return [event.to_dict() for event in reversed(recent)]


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
async def speak_announcement(
    announcement_id: int,
    language: Optional[str] = None,
    db: Session = Depends(get_db)
):
    db_announcement = db.query(Announcement).filter(Announcement.id == announcement_id).first()
    if not db_announcement:
        raise HTTPException(status_code=404, detail="Announcement not found")
    
    lang = language if language is not None else db_announcement.language
    voice = VOICE_MAP.get(lang)
    if voice is None:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported language code '{lang}'. Supported: {', '.join(sorted(VOICE_MAP))}"
        )
    
    communicate = edge_tts.Communicate(db_announcement.message, voice)
    audio = _audio_only(communicate)

    try:
        first = await audio.__anext__()
    except StopAsyncIteration:
        raise HTTPException(status_code=502, detail="Speech synthesis returned no audio")
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Speech synthesis failed: {exc}") from exc

    async def stream():
        yield first
        async for chunk in audio:
            yield chunk

    return StreamingResponse(stream(), media_type="audio/mpeg")

