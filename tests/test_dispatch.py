import math

import pytest

from backend.schemas import GeoPoint
from backend.services.dispatch import (
    EARTH_RADIUS_KM,
    PROVIDER_PRICING,
    DispatchValidationError,
    build_emergency_quote,
    calculate_fare,
    haversine_km,
)


URL = "/api/dispatch/emergency-quote"


def payload(pickup=(12.0, 77.0), dropoff=(12.1, 77.0)):
    return {
        "pickup": {"lat": pickup[0], "lon": pickup[1]},
        "dropoff": {"lat": dropoff[0], "lon": dropoff[1]},
    }


def test_haversine_and_fares_use_server_contract():
    assert haversine_km(0, 0, 1, 0) == pytest.approx(111.195, abs=1e-3)
    assert calculate_fare(PROVIDER_PRICING[0], 10) == 170
    assert calculate_fare(PROVIDER_PRICING[1], 10) == 160


def test_endpoint_returns_server_computed_provider_quotes(client):
    response = client.post(URL, json=payload())

    assert response.status_code == 200
    assert response.json() == {
        "currency": "INR",
        "distance_km": 11.12,
        "quotes": [
            {
                "provider": "uber",
                "provider_name": "Uber",
                "base_fare": 50.0,
                "per_km_rate": 12.0,
                "estimated_fare": 183.44,
            },
            {
                "provider": "ola",
                "provider_name": "Ola",
                "base_fare": 45.0,
                "per_km_rate": 11.5,
                "estimated_fare": 172.88,
            },
        ],
    }


def test_zero_and_max_distance_boundaries_are_supported(client):
    zero = client.post(URL, json=payload((12, 77), (12, 77)))
    assert zero.status_code == 200
    assert zero.json()["distance_km"] == 0
    assert [quote["estimated_fare"] for quote in zero.json()["quotes"]] == [50.0, 45.0]

    offset = math.degrees(100 / EARTH_RADIUS_KM)
    maximum = client.post(URL, json=payload((12, 77), (12 + offset, 77)))
    assert maximum.status_code == 200
    assert maximum.json()["distance_km"] == 100


def test_distance_beyond_limit_is_rejected(client):
    response = client.post(URL, json=payload((12, 77), (13, 77)))

    assert response.status_code == 422
    assert "at most 100 km" in response.json()["detail"]


@pytest.mark.parametrize(
    "section,field,value",
    [
        ("pickup", "lat", 90.001),
        ("pickup", "lon", 180.001),
        ("dropoff", "lat", "12.5"),
        ("dropoff", "lon", True),
    ],
)
def test_invalid_coordinates_are_rejected(client, section, field, value):
    body = payload()
    body[section][field] = value

    response = client.post(URL, json=body)

    assert response.status_code == 422


def test_client_cannot_supply_distance_or_fare(client):
    body = {**payload(), "distance_km": 1, "fare": 1}

    assert client.post(URL, json=body).status_code == 422


def test_non_finite_coordinates_return_422(client):
    response = client.post(
        URL,
        content='{"pickup":{"lat":NaN,"lon":77},"dropoff":{"lat":12.1,"lon":77}}',
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == 422