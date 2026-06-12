from fastapi import HTTPException, status
from typing import Any, Dict, Optional

class BaseAPIException(HTTPException):
    def __init__(self, status_code: int, detail: Any = None, headers: Optional[Dict[str, str]] = None) -> None:
        super().__init__(status_code=status_code, detail=detail, headers=headers)

class NotFoundException(BaseAPIException):
    def __init__(self, detail: Any = "Not Found") -> None:
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)

class BadRequestException(BaseAPIException):
    def __init__(self, detail: Any = "Bad Request") -> None:
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)

class ConflictException(BaseAPIException):
    def __init__(self, detail: Any = "Conflict") -> None:
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)

class InternalServerError(BaseAPIException):
    def __init__(self, detail: Any = "Internal Server Error") -> None:
        super().__init__(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail)

class RateLimitException(BaseAPIException):
    def __init__(self, detail: Any = "Too Many Requests") -> None:
        super().__init__(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=detail)

class CircuitOpenException(BaseAPIException):
    def __init__(self, detail: Any = "Service Unavailable") -> None:
        super().__init__(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=detail)
