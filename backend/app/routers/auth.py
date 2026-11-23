from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user_claims
from app.database.session import get_db_session
from app.repositories.clinic_repositories import (
    PenggunaRepository,
    model_to_pengguna_domain,
)
from app.schemas.schemas import LoginRequest
from app.services.auth_service import AuthService

router = APIRouter(prefix="/api/auth", tags=["Otentikasi"])


@router.post("/login")
async def login(
    payload: LoginRequest,
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    service = AuthService(session)
    try:
        return await service.authenticate(
            username=payload.username,
            password=payload.password,
            peran=payload.peran,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc


@router.get("/me")
async def get_me(
    claims: dict = Depends(get_current_user_claims),
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    repo = PenggunaRepository(session)
    model = await repo.get_by_id(claims["sub"])
    if model is None:
        raise HTTPException(status_code=404, detail="Pengguna tidak ditemukan.")
    domain = model_to_pengguna_domain(model)
    return domain.to_dict() | {
        "poli_praktik": model.poli_praktik,
        "shift_kerja": model.shift_kerja,
    }


@router.get("/dokter")
async def list_dokter(
    _: dict = Depends(get_current_user_claims),
    session: AsyncSession = Depends(get_db_session),
) -> list[dict]:
    repo = PenggunaRepository(session)
    models = await repo.list_dokter()
    return [
        model_to_pengguna_domain(m).to_dict() | {"poli_praktik": m.poli_praktik}
        for m in models
    ]
