from fastapi import APIRouter, HTTPException

from backend.schemas import EmergencyQuoteRequest, EmergencyQuoteResponse
from backend.services.dispatch import DispatchValidationError, build_emergency_quote

router = APIRouter(prefix="/api/dispatch", tags=["Dispatch"])


@router.post("/emergency-quote", response_model=EmergencyQuoteResponse)
def create_emergency_quote(request: EmergencyQuoteRequest):
    try:
        return build_emergency_quote(request.pickup, request.dropoff)
    except DispatchValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc