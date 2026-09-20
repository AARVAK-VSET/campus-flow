from sqlalchemy import Column, Integer, String
from backend.database import Base
from backend.timeutils import UTCDateTime, utcnow


class ParkingRecord(Base):
    __tablename__ = "parking_records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    car_number = Column(String, nullable=False)
    slot_number = Column(Integer, nullable=False)
    time_in = Column(UTCDateTime, default=utcnow)
    time_out = Column(UTCDateTime, nullable=True)
    status = Column(String, default="occupied")  # occupied, free

