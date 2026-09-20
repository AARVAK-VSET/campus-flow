from fastapi.testclient import TestClient

from backend.main import app


client = TestClient(app)


def test_invalid_year_and_slot_values_return_422():
    medical = {
        "student_name": "Validation Test",
        "branch": "CSE",
        "year": -5,
        "issue": "Fever",
    }
    parking = {"car_number": "VALIDATION-TEST", "slot_number": 99999999}

    medical_response = client.post("/api/medical/", json=medical)
    parking_response = client.post("/api/parking/", json=parking)

    assert medical_response.status_code == 422
    assert "year" in medical_response.text
    assert parking_response.status_code == 422
    assert "slot_number" in parking_response.text


def test_boundary_values_are_accepted_for_create_and_update():
    medical_response = client.post(
        "/api/medical/",
        json={
            "student_name": "Validation Test",
            "branch": "CSE",
            "year": 1,
            "issue": "Fever",
        },
    )
    assert medical_response.status_code == 200
    medical_id = medical_response.json()["id"]

    parking_response = client.post(
        "/api/parking/",
        json={"car_number": "VALIDATION-TEST", "slot_number": 1},
    )
    assert parking_response.status_code == 200
    parking_id = parking_response.json()["id"]

    try:
        assert client.put(
            f"/api/medical/{medical_id}", json={"year": 0}
        ).status_code == 422
        assert client.put(
            f"/api/parking/{parking_id}", json={"slot_number": 101}
        ).status_code == 422
        assert client.put(
            f"/api/medical/{medical_id}", json={"year": 5}
        ).status_code == 200
        assert client.put(
            f"/api/parking/{parking_id}", json={"slot_number": 100}
        ).status_code == 200
    finally:
        client.delete(f"/api/medical/{medical_id}")
        client.delete(f"/api/parking/{parking_id}")
