from typing import Any, Dict


class APIException(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail

    def to_dict(self) -> Dict[str, Any]:
        return {"error": self.detail}


class BadRequest(APIException):
    def __init__(self, detail: str):
        super().__init__(400, detail)


class Unauthorized(APIException):
    def __init__(self, detail: str = "Unauthorized"):
        super().__init__(401, detail)


class Forbidden(APIException):
    def __init__(self, detail: str = "Forbidden"):
        super().__init__(403, detail)


class NotFound(APIException):
    def __init__(self, detail: str = "Not found"):
        super().__init__(404, detail)


class Conflict(APIException):
    def __init__(self, detail: str = "Conflict"):
        super().__init__(409, detail)
