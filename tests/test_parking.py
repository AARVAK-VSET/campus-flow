from datetime import datetime, timezone

from backend.models.parking import ParkingRecord


def _now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _add(db_session, **fields):
    record = ParkingRecord(**fields)
    db_session.add(record)
    db_session.commit()
    db_session.refresh(record)
    return record


def _add_three_records(db_session):
    """Two vehicles currently parked, one that has already left."""
    first = _add(db_session, car_number="DL01AB1234", slot_number=1, status="occupied", time_in=_now())
    second = _add(db_session, car_number="MH12CD5678", slot_number=2, status="occupied", time_in=_now())
    left = _add(
        db_session,
        car_number="KA01EF9012",
        slot_number=3,
        status="free",
        time_in=_now(),
        time_out=_now(),
    )
    return first, second, left


def test_create_parking_record_defaults_to_occupied(client):
    response = client.post("/api/parking/", json={"car_number": "DL01AB1234", "slot_number": 4})

    assert response.status_code == 200
    body = response.json()
    assert body["id"] > 0
    assert body["status"] == "occupied"
    assert body["time_in"]
    assert body["time_out"] is None


def test_create_rejects_missing_slot_number(client):
    response = client.post("/api/parking/", json={"car_number": "DL01AB1234"})

    assert response.status_code == 422


def test_parking_filters_and_checkout(client, db_session):
    """Filters return the right vehicles, and a checked-out car leaves the active list."""
    first, second, _ = _add_three_records(db_session)

    # status=active returns exactly the two parked vehicles
    active = client.get("/api/parking/?status=active")
    assert active.status_code == 200, active.text
    assert {r["car_number"] for r in active.json()} == {"DL01AB1234", "MH12CD5678"}

    # car_number returns only that vehicle
    by_car = client.get("/api/parking/?car_number=DL01AB1234")
    assert by_car.status_code == 200
    assert [r["car_number"] for r in by_car.json()] == ["DL01AB1234"]

    # slot_number returns only that slot
    by_slot = client.get("/api/parking/?slot_number=2")
    assert by_slot.status_code == 200
    assert [r["slot_number"] for r in by_slot.json()] == [2]

    # filters combine
    combined = client.get("/api/parking/?status=active&slot_number=1")
    assert combined.status_code == 200
    assert [r["car_number"] for r in combined.json()] == ["DL01AB1234"]

    # after a vehicle checks out it disappears from the active results
    checkout = client.put(
        f"/api/parking/{first.id}",
        json={"status": "free", "time_out": _now().isoformat()},
    )
    assert checkout.status_code == 200

    after = client.get("/api/parking/?status=active")
    assert after.status_code == 200
    assert [r["id"] for r in after.json()] == [second.id]


def test_free_and_checked_out_filters_return_vehicles_that_left(client, db_session):
    _add_three_records(db_session)

    for status in ("free", "checked_out"):
        response = client.get(f"/api/parking/?status={status}")

        assert response.status_code == 200
        assert [r["car_number"] for r in response.json()] == ["KA01EF9012"]


def test_status_filter_ignores_case_and_surrounding_spaces(client, db_session):
    _add_three_records(db_session)

    response = client.get("/api/parking/?status=%20ACTIVE%20")

    assert response.status_code == 200
    assert len(response.json()) == 2


def test_invalid_status_returns_400(client):
    response = client.get("/api/parking/?status=unknown_status_xyz")

    assert response.status_code == 400
    assert "Invalid status" in response.json().get("detail", "")


def test_records_endpoint_alias_supports_status_filter(client, db_session):
    _add(db_session, car_number="UP16AA0001", slot_number=5, status="occupied", time_in=_now())

    response = client.get("/api/parking/records?status=active")

    assert response.status_code == 200
    assert [r["car_number"] for r in response.json()] == ["UP16AA0001"]


def test_no_filters_returns_every_record(client, db_session):
    _add_three_records(db_session)

    response = client.get("/api/parking/")

    assert response.status_code == 200
    assert len(response.json()) == 3


def test_blank_car_number_filter_is_ignored(client, db_session):
    _add_three_records(db_session)

    response = client.get("/api/parking/?car_number=%20")

    assert response.status_code == 200
    assert len(response.json()) == 3


def test_skip_and_limit_page_through_records(client, db_session):
    _add_three_records(db_session)

    page = client.get("/api/parking/?skip=1&limit=1").json()

    assert [r["car_number"] for r in page] == ["MH12CD5678"]


def test_update_missing_record_returns_404(client):
    response = client.put("/api/parking/999", json={"status": "free"})

    assert response.status_code == 404


def test_analytics_counts_occupied_and_free_slots(client, db_session, fake_insight):
    _add_three_records(db_session)

    response = client.get("/api/parking/analytics")

    assert response.status_code == 200
    body = response.json()
    assert body["stats"]["total"] == 3
    assert body["stats"]["occupied"] == 2
    assert body["stats"]["free"] == 1
    assert body["insights"] == fake_insight


def test_analytics_with_no_records(client, fake_insight):
    body = client.get("/api/parking/analytics").json()

    assert body["stats"]["total"] == 0
    assert body["insights"] == fake_insight


def test_detect_returns_ten_simulated_slots(client):
    response = client.post(
        "/api/parking/detect",
        files={"image": ("lot.jpg", b"not-a-real-image", "image/jpeg")},
    )

    assert response.status_code == 200
    body = response.json()
    assert [slot["id"] for slot in body["slots"]] == list(range(1, 11))
    for slot in body["slots"]:
        assert slot["status"] in {"occupied", "free"}
        assert (slot["car_number"] is not None) == (slot["status"] == "occupied")


def test_detect_requires_an_image(client):
    assert client.post("/api/parking/detect").status_code == 422
