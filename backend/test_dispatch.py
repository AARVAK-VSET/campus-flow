import math
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.schemas import GeoPoint
from backend.services.dispatch import (
    EARTH_RADIUS_KM,
    PROVIDER_PRICING,
    DispatchValidationError,
    build_emergency_quote,
    calculate_fare,
    haversine_km,
)

client = TestClient(app)
URL = "/api/dispatch/emergency-quote"

UBER, OLA = PROVIDER_PRICING

# 0.1 degrees of latitude is 11.1195 km, billed as 11.12 km:
#   Uber 50 + 12 * 11.12 = 183.44, Ola 45 + 11.5 * 11.12 = 172.88
EXPECTED_SHORT_HOP = {
    "currency": "INR",
    "distance_km": 11.12,
    "quotes": [
        {"provider": "uber", "provider_name": "Uber", "base_fare": 50.0, "per_km_rate": 12.0, "estimated_fare": 183.44},
        {"provider": "ola", "provider_name": "Ola", "base_fare": 45.0, "per_km_rate": 11.5, "estimated_fare": 172.88},
    ],
}


def _point(lat, lon):
    return GeoPoint(lat=lat, lon=lon)


def _payload(pickup=(12.0, 77.0), dropoff=(12.1, 77.0)):
    return {
        "pickup": {"lat": pickup[0], "lon": pickup[1]},
        "dropoff": {"lat": dropoff[0], "lon": dropoff[1]},
    }


def _payload_with(section, field, value):
    payload = _payload()
    payload[section][field] = value
    return payload


def _lat_offset_for_km(km):
    """Degrees of latitude spanning exactly `km` along a meridian."""
    return math.degrees(km / EARTH_RADIUS_KM)


# ---- Distance ----

def test_haversine_identical_points_is_zero():
    assert haversine_km(12.0, 77.0, 12.0, 77.0) == 0.0


def test_haversine_one_degree_of_latitude_and_equatorial_longitude():
    assert haversine_km(0, 0, 1, 0) == pytest.approx(111.195, abs=1e-3)
    assert haversine_km(0, 0, 0, 1) == pytest.approx(111.195, abs=1e-3)


def test_haversine_is_symmetric():
    forward = haversine_km(28.6139, 77.2090, 19.0760, 72.8777)
    backward = haversine_km(19.0760, 72.8777, 28.6139, 77.2090)
    assert forward == pytest.approx(backward)


@pytest.mark.parametrize("a,b", [((0, 0), (0, 180)), ((90, 0), (-90, 0)), ((45, 10), (-45, -170))])
def test_haversine_antipodal_points_do_not_raise(a, b):
    assert haversine_km(*a, *b) == pytest.approx(math.pi * EARTH_RADIUS_KM, rel=1e-9)


# ---- Fares ----

def test_fare_is_base_plus_per_km_rate():
    assert calculate_fare(UBER, Decimal("10")) == Decimal("170.00")
    assert calculate_fare(OLA, Decimal("10")) == Decimal("160.00")


def test_fare_at_zero_distance_is_base_fare():
    assert calculate_fare(UBER, Decimal("0")) == Decimal("50.00")
    assert calculate_fare(OLA, Decimal("0")) == Decimal("45.00")


def test_fare_rounds_half_up_to_paise():
    # 45 + 11.5 * 0.01 = 45.115: half-up gives 45.12 (banker's/float rounding gives 45.11)
    assert calculate_fare(OLA, Decimal("0.01")) == Decimal("45.12")


# ---- Quote service ----

def test_quote_prices_every_provider_on_server_computed_distance():
    assert build_emergency_quote(_point(12.0, 77.0), _point(12.1, 77.0)) == EXPECTED_SHORT_HOP


def test_zero_distance_quotes_base_fare_only():
    here = _point(12.0, 77.0)
    result = build_emergency_quote(here, here)
    assert result["distance_km"] == 0.0
    assert [q["estimated_fare"] for q in result["quotes"]] == [50.0, 45.0]


def test_distance_at_service_limit_is_accepted():
    result = build_emergency_quote(_point(12.0, 77.0), _point(12.0 + _lat_offset_for_km(100), 77.0))
    assert result["distance_km"] == 100.0
    assert [q["estimated_fare"] for q in result["quotes"]] == [1250.0, 1195.0]


def test_distance_just_under_service_limit_is_accepted():
    result = build_emergency_quote(_point(12.0, 77.0), _point(12.0 + _lat_offset_for_km(99.98), 77.0))
    assert result["distance_km"] == 99.98


def test_distance_just_over_service_limit_is_rejected():
    with pytest.raises(DispatchValidationError, match="at most 100 km"):
        build_emergency_quote(_point(12.0, 77.0), _point(12.0 + _lat_offset_for_km(100.02), 77.0))


@pytest.mark.parametrize("a,b", [((0, 0), (0, 180)), ((90, 0), (-90, 0))])
def test_antipodal_points_are_rejected_not_crashed(a, b):
    with pytest.raises(DispatchValidationError):
        build_emergency_quote(_point(*a), _point(*b))


# ---- Endpoint ----

def test_endpoint_returns_structured_provider_quotes():
    response = client.post(URL, json=_payload())
    assert response.status_code == 200
    assert response.json() == EXPECTED_SHORT_HOP


def test_endpoint_is_deterministic():
    first = client.post(URL, json=_payload()).json()
    assert all(client.post(URL, json=_payload()).json() == first for _ in range(5))


@pytest.mark.parametrize(
    "pickup,dropoff",
    [
        ((90, 0), (89.9, 0)),
        ((-90, 0), (-89.9, 0)),
        ((0, 180), (0, 179.9)),
        ((0, -180), (0, -179.9)),
    ],
)
def test_endpoint_accepts_coordinates_on_the_valid_boundary(pickup, dropoff):
    response = client.post(URL, json=_payload(pickup, dropoff))
    assert response.status_code == 200
    assert response.json()["distance_km"] == 11.12


def test_endpoint_accepts_distance_at_service_limit():
    response = client.post(URL, json=_payload(dropoff=(12.0 + _lat_offset_for_km(100), 77.0)))
    assert response.status_code == 200
    assert response.json()["distance_km"] == 100.0


def test_endpoint_rejects_distance_beyond_service_limit():
    delhi, mumbai = (28.6139, 77.2090), (19.0760, 72.8777)
    response = client.post(URL, json=_payload(pickup=delhi, dropoff=mumbai))
    assert response.status_code == 422
    assert "at most 100 km" in response.json()["detail"]


@pytest.mark.parametrize("section", ["pickup", "dropoff"])
@pytest.mark.parametrize(
    "field,value",
    [
        ("lat", 90.0001),
        ("lat", -90.0001),
        ("lat", 1e9),
        ("lon", 180.0001),
        ("lon", -180.0001),
        ("lon", 1e9),
        ("lat", "12.5"),
        ("lon", "abc"),
        ("lat", True),
        ("lon", None),
        ("lat", [12.0]),
    ],
)
def test_endpoint_rejects_invalid_coordinates(section, field, value):
    response = client.post(URL, json=_payload_with(section, field, value))
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", section, field]


@pytest.mark.parametrize("literal", ["NaN", "Infinity", "-Infinity"])
def test_endpoint_rejects_non_finite_coordinates(literal):
    body = '{"pickup": {"lat": %s, "lon": 77}, "dropoff": {"lat": 12.1, "lon": 77}}' % literal
    response = client.post(URL, content=body, headers={"Content-Type": "application/json"})
    assert response.status_code == 422


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"pickup": {"lat": 12.0, "lon": 77.0}},
        {"dropoff": {"lat": 12.1, "lon": 77.0}},
        {"pickup": {"lat": 12.0}, "dropoff": {"lat": 12.1, "lon": 77.0}},
        {"pickup": {"lon": 77.0}, "dropoff": {"lat": 12.1, "lon": 77.0}},
        {"pickup": None, "dropoff": None},
        {"pickup": [12.0, 77.0], "dropoff": [12.1, 77.0]},
    ],
)
def test_endpoint_rejects_missing_or_malformed_points(payload):
    assert client.post(URL, json=payload).status_code == 422


@pytest.mark.parametrize("extra", [{"distance_km": 0.1}, {"fare": 1}, {"provider": "uber"}])
def test_endpoint_rejects_client_supplied_distance_or_fare(extra):
    assert client.post(URL, json={**_payload(), **extra}).status_code == 422


def test_endpoint_rejects_unknown_field_on_a_point():
    payload = _payload()
    payload["pickup"]["altitude"] = 5
    assert client.post(URL, json=payload).status_code == 422
