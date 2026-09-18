from fastapi.testclient import TestClient
from main import app
from backend.database import Base, engine, SessionLocal
from backend.models.parking import ParkingRecord

# Ensure tables are created
Base.metadata.create_all(bind=engine)

client = TestClient(app)

def test_create_parking():
    response = client.post("/api/parking", json={"car_number": "TEST4321", "slot_number": 3})
    print(f"Status Code: {response.status_code}")
    print(f"Response Body: {response.json()}")

if __name__ == "__main__":
    test_create_parking()

