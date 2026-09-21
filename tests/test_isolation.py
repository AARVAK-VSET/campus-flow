"""Proves every test starts with an empty database (changes are rolled back).

The two tests below depend on running in this order (pytest runs tests in the
order they are written in the file).
"""

RECORD = {"student_name": "Asha", "branch": "CSE", "year": 2, "issue": "Fever"}


def test_a_writes_a_record_and_commits(client):
    response = client.post("/api/medical/", json=RECORD)

    assert response.status_code == 200
    assert len(client.get("/api/medical/").json()) == 1


def test_b_previous_test_left_nothing_behind(client):
    assert client.get("/api/medical/").json() == []
