import logging
import math
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

from backend.schemas import GeoPoint

logger = logging.getLogger(__name__)

EARTH_RADIUS_KM = 6371.0
CURRENCY = "INR"
# Emergency transport is a local hop; beyond this a per-km quote is not meaningful.
MAX_DISPATCH_DISTANCE_KM = Decimal("100")

_CENTS = Decimal("0.01")


class DispatchValidationError(ValueError):
    """The request is well-formed but cannot be priced (e.g. out of service range)."""


@dataclass(frozen=True)
class ProviderPricing:
    provider_id: str
    name: str
    base_fare: Decimal
    per_km_rate: Decimal


# Pricing models for each provider (carried over from the former frontend estimates).
PROVIDER_PRICING = (
    ProviderPricing("uber", "Uber", Decimal("50"), Decimal("12")),
    ProviderPricing("ola", "Ola", Decimal("45"), Decimal("11.5")),
)


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    # Clamp: rounding can push a slightly past 1 for near-antipodal points.
    return 2 * EARTH_RADIUS_KM * math.asin(min(1.0, math.sqrt(a)))


def _round_money(value: Decimal) -> Decimal:
    return value.quantize(_CENTS, rounding=ROUND_HALF_UP)


def calculate_fare(pricing: ProviderPricing, distance_km: Decimal) -> Decimal:
    return _round_money(pricing.base_fare + pricing.per_km_rate * distance_km)


def build_emergency_quote(pickup: GeoPoint, dropoff: GeoPoint) -> dict:
    """Price an emergency cab from pickup to dropoff with every configured provider.

    The distance is computed here from the coordinates (never taken from the
    client) and rounded to 10 m; fares are priced on that billable distance so
    the response can be audited from its own fields.
    """
    raw_km = haversine_km(pickup.lat, pickup.lon, dropoff.lat, dropoff.lon)
    distance_km = _round_money(Decimal(str(raw_km)))

    if distance_km > MAX_DISPATCH_DISTANCE_KM:
        logger.warning("Emergency quote rejected: distance_km=%s exceeds limit %s", distance_km, MAX_DISPATCH_DISTANCE_KM)
        raise DispatchValidationError(
            f"Pickup and dropoff are {distance_km} km apart; "
            f"emergency dispatch supports at most {MAX_DISPATCH_DISTANCE_KM} km."
        )

    quotes = [
        {
            "provider": p.provider_id,
            "provider_name": p.name,
            "base_fare": float(p.base_fare),
            "per_km_rate": float(p.per_km_rate),
            "estimated_fare": float(calculate_fare(p, distance_km)),
        }
        for p in PROVIDER_PRICING
    ]
    logger.info("Emergency quote generated: distance_km=%s providers=%d", distance_km, len(quotes))
    return {"currency": CURRENCY, "distance_km": float(distance_km), "quotes": quotes}
