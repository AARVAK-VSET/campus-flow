from sqlalchemy import Column, Integer, String, Text, Boolean
from backend.database import Base
from backend.timeutils import UTCDateTime, utcnow


class Announcement(Base):
    __tablename__ = "announcements"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    message = Column(Text, nullable=False)
    language = Column(String, default="en")
    repeat_interval = Column(Integer, default=0)  # seconds, 0 = no repeat
    is_active = Column(Boolean, default=True)
    created_at = Column(UTCDateTime, default=utcnow)

