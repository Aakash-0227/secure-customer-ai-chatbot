
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.services.security import verify_access_token


bearer_scheme = HTTPBearer()


def get_current_customer_id(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> int:
    customer_id = verify_access_token(credentials.credentials)

    if customer_id is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired access token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return customer_id
