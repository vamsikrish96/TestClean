from typing import Optional
from fastapi import Depends, HTTPException, Request
from app.models import UserRole
from app.schemas import CurrentUserSchema


def extract_bearer_token(request: Request) -> str:
    """Extract Bearer token from Authorization header."""
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(status_code=401, detail="Authorization header missing")

    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid Authorization header format")

    return parts[1]


def parse_mocked_token(token: str) -> CurrentUserSchema:
    """Parse mocked JWT token with format: user_id:role."""
    try:
        user_id, role_str = token.split(":")
        role = UserRole(role_str.lower())
        return CurrentUserSchema(user_id=user_id, role=role)
    except (ValueError, KeyError):
        raise HTTPException(status_code=401, detail="Invalid token format. Expected user_id:role")


def get_current_user(request: Request) -> CurrentUserSchema:
    """Dependency to extract and validate current user from Bearer token."""
    token = extract_bearer_token(request)
    return parse_mocked_token(token)


def require_role(*allowed_roles: UserRole):
    """Dependency factory to check if user has required role."""
    def check_role(current_user: CurrentUserSchema = Depends(get_current_user)) -> CurrentUserSchema:
        if current_user.role not in allowed_roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return current_user
    return check_role
