from sqlalchemy import Column, Integer, String
from backend.database import Base
from backend.timeutils import UTCDateTime, utcnow


class MedicalRecord(Base):
    __tablename__ = "medical_records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    student_name = Column(String, nullable=False)
    branch = Column(String, nullable=False)
    year = Column(Integer, nullable=False)
    issue = Column(String, nullable=False)
    date_time = Column(UTCDateTime, default=utcnow)
    severity = Column(String, default="low")  # low, medium, high, critical
    treatment_status = Column(String, default="pending")  # pending, treating, discharged
    parent_contact = Column(String, nullable=True)
    address = Column(String, nullable=True)

