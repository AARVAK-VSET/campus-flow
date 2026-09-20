from sqlalchemy import Column, Integer, String, DateTime, Index
from datetime import datetime
from backend.database import Base


class ParkingRecord(Base):
    __tablename__ = "parking_records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    car_number = Column(String, nullable=False, index=True)
    slot_number = Column(Integer, nullable=False)
    time_in = Column(DateTime, default=datetime.utcnow)
    time_out = Column(DateTime, nullable=True)
    status = Column(String, default="occupied", index=True)  # occupied, free

    __table_args__ = (
        Index("idx_parking_status", "status"),
        Index("idx_parking_car_number", "car_number"),
        Index("idx_parking_slot_status", "slot_number", "status"),
    )

