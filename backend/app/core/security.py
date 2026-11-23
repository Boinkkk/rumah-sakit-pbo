from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from app.core.config import ACCESS_TOKEN_EXPIRE_MINUTES, ALGORITHM, SECRET_KEY

bearer_scheme = HTTPBearer(auto_error=False)


def hash_password_sha256(password: str) -> str:
    """Enkripsi kata sandi menggunakan fungsi hash kriptografi SHA-256 (sesuai spesifikasi Tabel 2.2)."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def verify_password_sha256(plain_password: str, password_hash: str) -> bool:
    return hash_password_sha256(plain_password) == password_hash


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token autentikasi tidak valid atau telah kedaluwarsa.",
        ) from exc


async def get_current_user_claims(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> dict[str, Any]:
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Autentikasi diperlukan untuk mengakses sumber daya ini.",
        )
    return decode_access_token(credentials.credentials)


def require_roles(*allowed_roles: str):
    """Dependency RBAC untuk membatasi akses endpoint berdasarkan peran pengguna."""

    async def role_checker(
        claims: dict[str, Any] = Depends(get_current_user_claims),
    ) -> dict[str, Any]:
        peran = claims.get("peran")
        if peran not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Akses ditolak. Peran '{peran}' tidak memiliki izin untuk aksi ini.",
            )
        return claims

    return role_checker
