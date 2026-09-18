from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from backend.database import Base


class ParkingRecord(Base):
    __tablename__ = "parking_records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    car_number = Column(String, nullable=False)
    slot_number = Column(Integer, nullable=False)
    time_in = Column(DateTime, default=datetime.utcnow)
    time_out = Column(DateTime, nullable=True)
    status = Column(String, default="occupied")  # occupied, free

