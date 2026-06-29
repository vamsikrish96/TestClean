from typing import Optional, Callable, Any
from fastapi import Request, Header
from functools import wraps
from app.config import UserRole, VALID_ROLES
from app.utils.errors import Unauthorized, Forbidden


class AuthContext:
    def __init__(self, user_id: str, role: str):
        self.user_id = user_id
        self.role = role


async def extract_auth_headers(request: Request) -> Optional[AuthContext]:
    user_id = request.headers.get("X-User-ID")
    role = request.headers.get("X-User-Role")

    if not user_id or not role:
        return None

    if role not in VALID_ROLES:
        return None

    return AuthContext(user_id=user_id, role=role)


def require_role(*allowed_roles: str) -> Callable:
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            request: Request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break

            if not request:
                if "request" in kwargs:
                    request = kwargs["request"]

            if not request:
                raise Unauthorized("Request context not found")

            auth = await extract_auth_headers(request)
            if not auth:
                raise Unauthorized("Missing or invalid authentication headers")

            if auth.role not in allowed_roles:
                raise Forbidden(f"User role '{auth.role}' is not allowed for this operation")

            kwargs["auth"] = auth
            return await func(*args, **kwargs)

        return wrapper

    return decorator


def require_employee(func: Callable) -> Callable:
    return require_role(UserRole.EMPLOYEE.value)(func)


def require_manager(func: Callable) -> Callable:
    return require_role(UserRole.MANAGER.value)(func)


def require_finance(func: Callable) -> Callable:
    return require_role(UserRole.FINANCE.value)(func)
