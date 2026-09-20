from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional
from datetime import datetime, date


# ---- Medical ----
class MedicalRecordBase(BaseModel):
    student_name: str
    branch: str
    year: int
    issue: str
    severity: str = "low"
    treatment_status: str = "pending"
    parent_contact: Optional[str] = None
    address: Optional[str] = None


class MedicalRecordCreate(MedicalRecordBase):
    pass


class MedicalRecordUpdate(BaseModel):
    student_name: Optional[str] = None
    branch: Optional[str] = None
    year: Optional[int] = None
    issue: Optional[str] = None
    severity: Optional[str] = None
    treatment_status: Optional[str] = None
    parent_contact: Optional[str] = None
    address: Optional[str] = None


class MedicalRecordOut(MedicalRecordBase):
    id: int
    date_time: datetime

    class Config:
        from_attributes = True


# ---- Stationery ----
class StationeryItemBase(BaseModel):
    item_name: str
    price: float
    quantity: int = 0
    category: Optional[str] = None
    student_demand: int = 0


class StationeryItemCreate(StationeryItemBase):
    pass


class StationeryItemUpdate(BaseModel):
    item_name: Optional[str] = None
    price: Optional[float] = None
    quantity: Optional[int] = None
    category: Optional[str] = None
    student_demand: Optional[int] = None


class StationeryItemOut(StationeryItemBase):
    id: int
    purchase_date: date

    class Config:
        from_attributes = True


# ---- Announcement ----
class AnnouncementBase(BaseModel):
    message: str
    language: str = "en"
    repeat_interval: int = 0
    is_active: bool = True


class AnnouncementCreate(AnnouncementBase):
    pass


class AnnouncementOut(AnnouncementBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ---- Parking ----
class ParkingRecordBase(BaseModel):
    car_number: str
    slot_number: int
    status: str = "occupied"


class ParkingRecordCreate(ParkingRecordBase):
    pass


class ParkingRecordUpdate(BaseModel):
    car_number: Optional[str] = None
    slot_number: Optional[int] = None
    time_out: Optional[datetime] = None
    status: Optional[str] = None


class ParkingRecordOut(ParkingRecordBase):
    id: int
    time_in: datetime
    time_out: Optional[datetime] = None

    class Config:
        from_attributes = True


# ---- Dispatch ----
class GeoPoint(BaseModel):
    """A validated WGS84 coordinate; strict so strings, booleans and NaN/inf are rejected."""
    model_config = ConfigDict(extra="forbid")

    lat: float = Field(..., ge=-90, le=90, strict=True, allow_inf_nan=False)
    lon: float = Field(..., ge=-180, le=180, strict=True, allow_inf_nan=False)


class EmergencyQuoteRequest(BaseModel):
    # Distance and fares are always computed server-side; unknown fields
    # (e.g. a client-supplied distance_km) are rejected rather than ignored.
    model_config = ConfigDict(extra="forbid")

    pickup: GeoPoint
    dropoff: GeoPoint


class ProviderQuote(BaseModel):
    provider: str
    provider_name: str
    base_fare: float
    per_km_rate: float
    estimated_fare: float


class EmergencyQuoteResponse(BaseModel):
    currency: str
    distance_km: float
    quotes: List[ProviderQuote]

