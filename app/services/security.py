
import os
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("JWT_SECRET_KEY")

if not SECRET_KEY or len(SECRET_KEY) < 32:
    raise RuntimeError(
        "Set JWT_SECRET_KEY to a randomly generated secret "
        "of at least 32 characters in your .env file."
    )

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def create_access_token(customer_id: int) -> str:
    """Create a signed access token that expires in 30 minutes."""
    now = datetime.now(timezone.utc)

    payload = {
        "sub": str(customer_id),
        "iat": now,
        "exp": now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    }

    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def verify_access_token(token: str) -> int | None:
    """Validate a token and return its customer ID."""
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
        )

        subject = payload.get("sub")
        if not subject:
            return None

        customer_id = int(subject)
        if customer_id <= 0:
            return None

        return customer_id

    except (JWTError, ValueError, TypeError):
        return None
