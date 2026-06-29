import base64
import json
from typing import Optional, Callable
from fastapi import Header, HTTPException, status, Depends

BEARER_PREFIX = "Bearer "


class TokenPayload:
    def __init__(self, user_id: str, role: str):
        self.user_id = user_id
        self.role = role


def decode_token(authorization: str) -> TokenPayload:
    if not authorization or not authorization.startswith(BEARER_PREFIX):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header"
        )

    token = authorization[len(BEARER_PREFIX):]
    try:
        payload_bytes = base64.b64decode(token)
        payload_str = payload_bytes.decode('utf-8')
        payload = json.loads(payload_str)

        if 'user_id' not in payload or 'role' not in payload:
            raise ValueError("Missing required fields in token")

        return TokenPayload(user_id=payload['user_id'], role=payload['role'])
    except (ValueError, json.JSONDecodeError, UnicodeDecodeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token format"
        )


def get_current_user(authorization: Optional[str] = Header(None)) -> TokenPayload:
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required"
        )
    return decode_token(authorization)


def require_role(*allowed_roles: str) -> Callable:
    def role_checker(token: TokenPayload = Depends(get_current_user)) -> TokenPayload:
        if token.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role: {', '.join(allowed_roles)}"
            )
        return token
    return role_checker
