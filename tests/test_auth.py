import pytest
from fastapi import Request
from app.auth.middleware import extract_auth_headers, AuthContext
from app.utils.errors import Unauthorized, Forbidden


class TestExtractAuthHeaders:
    @pytest.mark.asyncio
    async def test_valid_headers(self):
        request = Request(
            scope={
                "type": "http",
                "headers": [
                    (b"x-user-id", b"emp123"),
                    (b"x-user-role", b"employee"),
                ],
            }
        )
        auth = await extract_auth_headers(request)
        assert auth is not None
        assert auth.user_id == "emp123"
        assert auth.role == "employee"

    @pytest.mark.asyncio
    async def test_missing_user_id(self):
        request = Request(
            scope={
                "type": "http",
                "headers": [(b"x-user-role", b"employee")],
            }
        )
        auth = await extract_auth_headers(request)
        assert auth is None

    @pytest.mark.asyncio
    async def test_missing_role(self):
        request = Request(
            scope={
                "type": "http",
                "headers": [(b"x-user-id", b"emp123")],
            }
        )
        auth = await extract_auth_headers(request)
        assert auth is None

    @pytest.mark.asyncio
    async def test_invalid_role(self):
        request = Request(
            scope={
                "type": "http",
                "headers": [
                    (b"x-user-id", b"emp123"),
                    (b"x-user-role", b"admin"),
                ],
            }
        )
        auth = await extract_auth_headers(request)
        assert auth is None

    @pytest.mark.asyncio
    async def test_all_valid_roles(self):
        for role in ["employee", "manager", "finance"]:
            request = Request(
                scope={
                    "type": "http",
                    "headers": [
                        (b"x-user-id", b"user123"),
                        (b"x-user-role", role.encode()),
                    ],
                }
            )
            auth = await extract_auth_headers(request)
            assert auth is not None
            assert auth.role == role

    @pytest.mark.asyncio
    async def test_empty_user_id(self):
        request = Request(
            scope={
                "type": "http",
                "headers": [
                    (b"x-user-id", b""),
                    (b"x-user-role", b"employee"),
                ],
            }
        )
        auth = await extract_auth_headers(request)
        assert auth is None

    @pytest.mark.asyncio
    async def test_empty_role(self):
        request = Request(
            scope={
                "type": "http",
                "headers": [
                    (b"x-user-id", b"emp123"),
                    (b"x-user-role", b""),
                ],
            }
        )
        auth = await extract_auth_headers(request)
        assert auth is None
