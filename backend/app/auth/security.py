"""Password hashing, JWT, secret encryption, and random password generation."""

import secrets
import string
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from cryptography.fernet import Fernet, InvalidToken
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import get_settings

ALGORITHM = "HS256"

# Token "audiences" distinguish admin sessions from demo-user call tokens.
AUDIENCE_ADMIN = "admin"
AUDIENCE_CALL = "call"

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# --- Passwords --------------------------------------------------------------

def hash_password(password: str) -> str:
    return _pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return _pwd_context.verify(plain, hashed)
    except ValueError:
        return False


def generate_password(length: int = 16) -> str:
    """Generate a readable random password (letters + digits)."""
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


# --- JWT --------------------------------------------------------------------

def create_token(subject: str, audience: str, expires_minutes: int, **claims: Any) -> str:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": subject,
        "aud": audience,
        "iat": now,
        "exp": now + timedelta(minutes=expires_minutes),
        **claims,
    }
    return jwt.encode(payload, settings.auth_jwt_secret, algorithm=ALGORITHM)


def decode_token(token: str, audience: str) -> Optional[dict]:
    settings = get_settings()
    try:
        return jwt.decode(
            token,
            settings.auth_jwt_secret,
            algorithms=[ALGORITHM],
            audience=audience,
        )
    except JWTError:
        return None


# --- Secret encryption (Fernet) ---------------------------------------------

def _fernet() -> Optional[Fernet]:
    key = get_settings().secrets_encryption_key
    if not key:
        return None
    return Fernet(key.encode() if isinstance(key, str) else key)


def encrypt_secret(value: str) -> str:
    f = _fernet()
    if not f:
        raise RuntimeError("SECRETS_ENCRYPTION_KEY is not configured.")
    return f.encrypt(value.encode()).decode()


def decrypt_secret(token: str) -> str:
    f = _fernet()
    if not f:
        raise RuntimeError("SECRETS_ENCRYPTION_KEY is not configured.")
    try:
        return f.decrypt(token.encode()).decode()
    except InvalidToken as exc:
        raise RuntimeError("Failed to decrypt secret.") from exc
