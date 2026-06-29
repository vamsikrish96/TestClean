import base64
import json
import pytest
from fastapi import HTTPException
from app.auth import decode_token, TokenPayload


class TestTokenDecoding:
    def test_decode_valid_token(self):
        payload = {"user_id": "emp_123", "role": "employee"}
        encoded = base64.b64encode(json.dumps(payload).encode()).decode()
        token = f"Bearer {encoded}"

        result = decode_token(token)
        assert result.user_id == "emp_123"
        assert result.role == "employee"

    def test_missing_bearer_prefix(self):
        payload = {"user_id": "emp_123", "role": "employee"}
        encoded = base64.b64encode(json.dumps(payload).encode()).decode()

        with pytest.raises(HTTPException) as exc_info:
            decode_token(encoded)
        assert exc_info.value.status_code == 401

    def test_invalid_base64(self):
        with pytest.raises(HTTPException) as exc_info:
            decode_token("Bearer invalid_base64!!!")
        assert exc_info.value.status_code == 401

    def test_missing_required_field(self):
        payload = {"user_id": "emp_123"}
        encoded = base64.b64encode(json.dumps(payload).encode()).decode()
        token = f"Bearer {encoded}"

        with pytest.raises(HTTPException) as exc_info:
            decode_token(token)
        assert exc_info.value.status_code == 401

    def test_empty_token(self):
        with pytest.raises(HTTPException) as exc_info:
            decode_token("")
        assert exc_info.value.status_code == 401

    def test_none_token(self):
        with pytest.raises(HTTPException) as exc_info:
            decode_token(None)
        assert exc_info.value.status_code == 401


class TestTokenPayload:
    def test_token_payload_creation(self):
        payload = TokenPayload("emp_001", "employee")
        assert payload.user_id == "emp_001"
        assert payload.role == "employee"
