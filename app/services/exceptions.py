from __future__ import annotations

from typing import Mapping


class ServiceError(Exception):
    status_code = 400

    def __init__(self, message: str, *, details: Mapping[str, str] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = dict(details) if details is not None else None


class BadRequestError(ServiceError):
    status_code = 400


class AuthenticationRequiredError(ServiceError):
    status_code = 401


class PermissionDeniedError(ServiceError):
    status_code = 403


class NotFoundError(ServiceError):
    status_code = 404


class ConflictError(ServiceError):
    status_code = 409


class ValidationError(ServiceError):
    status_code = 422
