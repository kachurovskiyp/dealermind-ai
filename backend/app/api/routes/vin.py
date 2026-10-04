from fastapi import APIRouter, HTTPException, status

from app.schemas.vin import (
    CepikHistoryPrepareRead,
    CepikHistoryPrepareRequest,
    VinDecodeRead,
    VinDecodeRequest,
)
from app.services.vin import decode_vin, prepare_cepik_history

router = APIRouter(prefix="/vin", tags=["VIN and CEPiK"])


@router.post("/decode", response_model=VinDecodeRead)
def decode(payload: VinDecodeRequest) -> VinDecodeRead:
    return decode_vin(payload.vin)


@router.post("/cepik/prepare", response_model=CepikHistoryPrepareRead)
def cepik_prepare(payload: CepikHistoryPrepareRequest) -> CepikHistoryPrepareRead:
    try:
        return prepare_cepik_history(
            payload.vin, payload.registration_number, payload.first_registration_date
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
