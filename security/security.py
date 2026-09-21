from datetime import datetime, timedelta, timezone
from typing import Optional
import bcrypt
import jwt

SECRET_KEY = "KeyUser-2026vp"
ALGORITHM = "HS256"

def generar_hash_contrasena(password: str) -> bytes:
    password_bytes = password.encode("utf-8")

    salt = bcrypt.gensalt()

    return bcrypt.hashpw(password_bytes, salt)


def verificar_contrasena(plain_password: str, hashed_password: bytes) -> bool:
    """
    Compara el String que manda el usuario al loguearse
    contra los bytes que tienes guardados en la base de datos.
    """
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password)


def crear_token_acceso(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
