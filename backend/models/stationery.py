from sqlalchemy import Column, Integer, String, Float, Date
from datetime import date
from backend.database import Base


class StationeryItem(Base):
    __tablename__ = "stationery_items"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    item_name = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    quantity = Column(Integer, nullable=False, default=0)
    category = Column(String, nullable=True)
    purchase_date = Column(Date, default=date.today)
    student_demand = Column(Integer, default=0)

