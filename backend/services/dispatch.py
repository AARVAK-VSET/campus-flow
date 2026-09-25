import math
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

from backend.schemas import GeoPoint

EARTH_RADIUS_KM = 6371.0
MAX_DISPATCH_DISTANCE_KM = Decimal("100")
_MONEY = Decimal("0.01")


class DispatchValidationError(ValueError):
    """Raised when a valid coordinate pair cannot be priced."""


@dataclass(frozen=True)
class ProviderPricing:
    provider_id: str
    name: str
    base_fare: Decimal
    per_km_rate: Decimal


PROVIDER_PRICING = (
    ProviderPricing("uber", "Uber", Decimal("50"), Decimal("12")),
    ProviderPricing("ola", "Ola", Decimal("45"), Decimal("11.5")),
)


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    first_latitude = math.radians(lat1)
    second_latitude = math.radians(lat2)
    latitude_delta = math.radians(lat2 - lat1)
    longitude_delta = math.radians(lon2 - lon1)
    haversine = (
        math.sin(latitude_delta / 2) ** 2
        + math.cos(first_latitude)
        * math.cos(second_latitude)
        * math.sin(longitude_delta / 2) ** 2
    )
    return 2 * EARTH_RADIUS_KM * math.asin(min(1.0, math.sqrt(haversine)))


def _round_money(value: Decimal) -> Decimal:
    return value.quantize(_MONEY, rounding=ROUND_HALF_UP)


def calculate_fare(pricing: ProviderPricing, distance_km: Decimal) -> Decimal:
    return _round_money(pricing.base_fare + pricing.per_km_rate * distance_km)


def build_emergency_quote(pickup: GeoPoint, dropoff: GeoPoint) -> dict:
    raw_distance = haversine_km(pickup.lat, pickup.lon, dropoff.lat, dropoff.lon)
    distance_km = _round_money(Decimal(str(raw_distance)))

    if distance_km > MAX_DISPATCH_DISTANCE_KM:
        raise DispatchValidationError(
            f"Pickup and dropoff are {distance_km} km apart; "
            f"emergency dispatch supports at most {MAX_DISPATCH_DISTANCE_KM} km."
        )

    quotes = [
        {
            "provider": pricing.provider_id,
            "provider_name": pricing.name,
            "base_fare": float(pricing.base_fare),
            "per_km_rate": float(pricing.per_km_rate),
            "estimated_fare": float(calculate_fare(pricing, distance_km)),
        }
        for pricing in PROVIDER_PRICING
    ]
    return {"currency": "INR", "distance_km": float(distance_km), "quotes": quotes}