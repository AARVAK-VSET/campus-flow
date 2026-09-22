from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from backend.database import Base


class MedicalRecord(Base):
    __tablename__ = "medical_records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    student_name = Column(String, nullable=False, index=True)
    branch = Column(String, nullable=False, index=True)
    year = Column(Integer, nullable=False)
    issue = Column(String, nullable=False)
    date_time = Column(DateTime, default=datetime.utcnow)
    severity = Column(String, default="low", index=True)  # low, medium, high, critical
    treatment_status = Column(String, default="pending", index=True)  # pending, treating, discharged
    parent_contact = Column(String, nullable=True)
    address = Column(String, nullable=True)

