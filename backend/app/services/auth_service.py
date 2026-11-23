from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.repositories.clinic_repositories import (
    PenggunaRepository,
    model_to_pengguna_domain,
)


class AuthService:
    def __init__(self, session: AsyncSession):
        self._session = session
        self._repo = PenggunaRepository(session)

    async def authenticate(
        self,
        username: str,
        password: str,
        peran: str | None = None,
    ) -> dict:
        model = await self._repo.get_by_username(username)
        if model is None:
            raise ValueError("Username atau kata sandi tidak valid.")

        pengguna = model_to_pengguna_domain(model)
        if not pengguna.verifikasi_login(password):
            raise ValueError("Username atau kata sandi tidak valid.")

        if peran and pengguna.peran != peran:
            raise ValueError(
                f"Akun '{username}' terdaftar sebagai '{pengguna.peran}', bukan '{peran}'."
            )

        token = create_access_token(
            {
                "sub": pengguna.id_pengguna,
                "username": pengguna.username,
                "nama_lengkap": pengguna.nama_lengkap,
                "peran": pengguna.peran,
            }
        )
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": pengguna.to_dict() | {"poli_praktik": model.poli_praktik, "shift_kerja": model.shift_kerja},
        }
