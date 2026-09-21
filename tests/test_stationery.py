import backend.routers.stationery as stationery_router

ITEM = {
    "item_name": "Notebook",
    "price": 49.5,
    "quantity": 25,
    "category": "Paper",
    "student_demand": 7,
}


def _create(client, **overrides):
    response = client.post("/api/stationery/", json={**ITEM, **overrides})
    assert response.status_code == 200, response.text
    return response.json()


def test_create_item_returns_saved_item(client):
    body = _create(client)

    assert body["id"] > 0
    assert body["item_name"] == "Notebook"
    assert body["price"] == 49.5
    assert body["quantity"] == 25
    assert body["purchase_date"]


def test_create_uses_defaults_for_optional_fields(client):
    response = client.post("/api/stationery/", json={"item_name": "Pen", "price": 10})

    assert response.status_code == 200
    body = response.json()
    assert body["quantity"] == 0
    assert body["student_demand"] == 0
    assert body["category"] is None


def test_create_rejects_missing_price(client):
    response = client.post("/api/stationery/", json={"item_name": "Pen"})

    assert response.status_code == 422


def test_create_rejects_non_numeric_price(client):
    response = client.post("/api/stationery/", json={"item_name": "Pen", "price": "cheap"})

    assert response.status_code == 422


def test_list_returns_created_items_and_supports_paging(client):
    for name in ("Pen", "Ruler", "Eraser"):
        _create(client, item_name=name)

    everything = client.get("/api/stationery/").json()
    page = client.get("/api/stationery/?skip=1&limit=1").json()

    assert [i["item_name"] for i in everything] == ["Pen", "Ruler", "Eraser"]
    assert [i["item_name"] for i in page] == ["Ruler"]


def test_update_changes_only_the_fields_sent(client):
    item = _create(client)

    response = client.put(f"/api/stationery/{item['id']}", json={"quantity": 3})

    assert response.status_code == 200
    updated = response.json()
    assert updated["quantity"] == 3
    assert updated["item_name"] == "Notebook"
    assert updated["price"] == 49.5


def test_update_missing_item_returns_404(client):
    assert client.put("/api/stationery/999", json={"quantity": 1}).status_code == 404


def test_delete_removes_the_item(client):
    item = _create(client)

    response = client.delete(f"/api/stationery/{item['id']}")

    assert response.status_code == 200
    assert client.get("/api/stationery/").json() == []


def test_delete_missing_item_returns_404(client):
    assert client.delete("/api/stationery/999").status_code == 404


def test_analytics_reports_low_stock_and_ai_insight(client, fake_insight):
    _create(client, item_name="Notebook", quantity=25, student_demand=7)
    _create(client, item_name="Pencil", quantity=3, category="Writing", student_demand=20)

    response = client.get("/api/stationery/analytics")

    assert response.status_code == 200
    body = response.json()
    assert body["stats"]["total"] == 2
    assert body["stats"]["top_demand"][0]["name"] == "Pencil"
    assert [i["name"] for i in body["stats"]["low_stock"]] == ["Pencil"]
    assert body["insights"] == fake_insight


def test_proposal_only_includes_low_stock_items(client, monkeypatch):
    _create(client, item_name="Notebook", quantity=25)
    _create(client, item_name="Pencil", quantity=3, category="Writing")
    captured = {}

    async def fake_generate_proposal(items):
        captured["items"] = items
        return "PROPOSAL TEXT"

    monkeypatch.setattr(stationery_router, "generate_proposal", fake_generate_proposal)

    response = client.post("/api/stationery/proposal")

    assert response.status_code == 200
    assert response.json() == {"proposal": "PROPOSAL TEXT"}
    assert captured["items"] == [{"name": "Pencil", "stock": 3, "category": "Writing"}]


def test_proposal_uses_ai_service(client, fake_insight):
    _create(client, item_name="Pencil", quantity=3)

    response = client.post("/api/stationery/proposal")

    assert response.json() == {"proposal": fake_insight}


def test_voice_command_is_forwarded_to_the_parser(client, monkeypatch):
    calls = []

    async def fake_parse_voice_command(text, context):
        calls.append((text, context))
        return {"action": "search", "data": {"item_name": "Pen"}}

    monkeypatch.setattr(stationery_router, "parse_voice_command", fake_parse_voice_command)

    response = client.post("/api/stationery/voice", params={"command": "find a pen"})

    assert response.status_code == 200
    assert response.json() == {"action": "search", "data": {"item_name": "Pen"}}
    assert calls == [("find a pen", "stationery")]


def test_voice_command_requires_the_command_parameter(client):
    assert client.post("/api/stationery/voice").status_code == 422
