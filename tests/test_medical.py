import backend.routers.medical as medical_router

RECORD = {
    "student_name": "Asha Verma",
    "branch": "CSE",
    "year": 2,
    "issue": "Fever",
    "severity": "medium",
}


def _create(client, **overrides):
    response = client.post("/api/medical/", json={**RECORD, **overrides})
    assert response.status_code == 200, response.text
    return response.json()


def test_create_record_returns_saved_record_with_defaults(client):
    body = _create(client)

    assert body["id"] > 0
    assert body["student_name"] == "Asha Verma"
    assert body["severity"] == "medium"
    assert body["treatment_status"] == "pending"
    assert body["parent_contact"] is None
    assert body["date_time"]


def test_create_rejects_missing_required_fields(client):
    response = client.post("/api/medical/", json={"student_name": "Asha"})

    assert response.status_code == 422


def test_create_rejects_wrong_field_type(client):
    response = client.post("/api/medical/", json={**RECORD, "year": "second"})

    assert response.status_code == 422


def test_list_is_empty_at_start(client):
    assert client.get("/api/medical/").json() == []


def test_list_returns_created_records(client):
    _create(client, student_name="Asha")
    _create(client, student_name="Ravi")

    names = [r["student_name"] for r in client.get("/api/medical/").json()]

    assert names == ["Asha", "Ravi"]


def test_list_supports_skip_and_limit(client):
    for name in ("A", "B", "C"):
        _create(client, student_name=name)

    page = client.get("/api/medical/?skip=1&limit=1").json()

    assert [r["student_name"] for r in page] == ["B"]


def test_update_changes_only_the_fields_sent(client):
    record = _create(client)

    response = client.put(f"/api/medical/{record['id']}", json={"treatment_status": "treating"})

    assert response.status_code == 200
    updated = response.json()
    assert updated["treatment_status"] == "treating"
    assert updated["student_name"] == "Asha Verma"
    assert updated["issue"] == "Fever"


def test_update_missing_record_returns_404(client):
    response = client.put("/api/medical/999", json={"issue": "Cold"})

    assert response.status_code == 404


def test_delete_removes_the_record(client):
    record = _create(client)

    response = client.delete(f"/api/medical/{record['id']}")

    assert response.status_code == 200
    assert client.get("/api/medical/").json() == []


def test_delete_missing_record_returns_404(client):
    assert client.delete("/api/medical/999").status_code == 404


def test_analytics_returns_stats_and_ai_insight(client, fake_insight):
    _create(client, issue="Fever")
    _create(client, issue="Fever", severity="high")
    _create(client, issue="Cough")

    response = client.get("/api/medical/analytics")

    assert response.status_code == 200
    body = response.json()
    assert body["stats"]["total"] == 3
    assert body["stats"]["by_issue"][0] == {"name": "Fever", "count": 2}
    assert {s["name"]: s["count"] for s in body["stats"]["by_severity"]} == {"medium": 2, "high": 1}
    assert body["insights"] == fake_insight


def test_analytics_with_no_records(client, fake_insight):
    body = client.get("/api/medical/analytics").json()

    assert body["stats"]["total"] == 0
    assert body["insights"] == fake_insight


def test_voice_command_is_forwarded_to_the_parser(client, monkeypatch):
    calls = []

    async def fake_parse_voice_command(text, context):
        calls.append((text, context))
        return {"action": "create", "data": {"student_name": "Asha"}}

    monkeypatch.setattr(medical_router, "parse_voice_command", fake_parse_voice_command)

    response = client.post("/api/medical/voice", params={"command": "add a record for Asha"})

    assert response.status_code == 200
    assert response.json() == {"action": "create", "data": {"student_name": "Asha"}}
    assert calls == [("add a record for Asha", "medical")]


def test_voice_command_requires_the_command_parameter(client):
    assert client.post("/api/medical/voice").status_code == 422
