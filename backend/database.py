from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SQLALCHEMY_DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'campus.db')}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def init_db():
    from sqlalchemy import text
    Base.metadata.create_all(bind=engine)
    try:
        with engine.connect() as conn:
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_parking_status ON parking_records (status)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_parking_car_number ON parking_records (car_number)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_parking_slot_status ON parking_records (slot_number, status)"))
            conn.commit()
    except Exception:
        pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

