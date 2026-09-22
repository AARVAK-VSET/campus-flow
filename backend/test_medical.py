from fastapi.testclient import TestClient
from backend.main import app
from backend.database import Base, engine, SessionLocal
from backend.models.medical import MedicalRecord

Base.metadata.create_all(bind=engine)
client = TestClient(app)

def setup_db():
    db = SessionLocal()
    db.query(MedicalRecord).delete()
    db.commit()
    
    records = [
        MedicalRecord(student_name="Alice Smith", branch="CS", year=1, issue="Fever", severity="low", treatment_status="pending"),
        MedicalRecord(student_name="Bob Jones", branch="ME", year=2, issue="Cut", severity="medium", treatment_status="treating"),
        MedicalRecord(student_name="Charlie Smith", branch="CS", year=3, issue="Headache", severity="low", treatment_status="discharged"),
        MedicalRecord(student_name="Diana Prince", branch="EE", year=4, issue="Burn", severity="high", treatment_status="treating"),
        MedicalRecord(student_name="Eve Adams", branch="CS", year=1, issue="Cough", severity="low", treatment_status="pending"),
    ]
    db.add_all(records)
    db.commit()
    db.close()

def test_medical_filters_and_pagination():
    setup_db()
    
    # Test substring ilike search
    res = client.get("/api/medical/?student_name=smith")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 2
    assert {"Alice Smith", "Charlie Smith"} == {r["student_name"] for r in data}
    
    # Test multiple filters (AND semantics)
    res = client.get("/api/medical/?branch=CS&severity=low")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 3
    
    res = client.get("/api/medical/?branch=CS&severity=low&treatment_status=pending")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 2
    assert {"Alice Smith", "Eve Adams"} == {r["student_name"] for r in data}
    
    # Test pagination boundaries
    res = client.get("/api/medical/?limit=2")
    assert res.status_code == 200
    assert len(res.json()) == 2
    
    res = client.get("/api/medical/?skip=4&limit=2")
    assert res.status_code == 200
    assert len(res.json()) == 1
    
    res = client.get("/api/medical/?skip=10&limit=5")
    assert res.status_code == 200
    assert len(res.json()) == 0

