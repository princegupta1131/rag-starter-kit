"""
One error format for the whole API:

    {"error": {"code": "not_found", "message": "Collection not found"}}

Raise AppError (or a subclass) anywhere; main.py turns it into that response.
"""
import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.providers.base import ProviderError

log = logging.getLogger(__name__)


class AppError(Exception):
    status = 400
    code = "bad_request"

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class NotFound(AppError):
    status = 404
    code = "not_found"


class Conflict(AppError):
    status = 409
    code = "conflict"


def _error(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse({"error": {"code": code, "message": message}}, status_code=status)


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error(_: Request, e: AppError):
        return _error(e.status, e.code, e.message)

    @app.exception_handler(RequestValidationError)
    async def _validation(_: Request, e: RequestValidationError):
        first = e.errors()[0]
        field = ".".join(str(p) for p in first["loc"] if p != "body")
        return _error(422, "invalid_request", f"{field}: {first['msg']}")

    @app.exception_handler(ProviderError)
    async def _provider(_: Request, e: ProviderError):
        log.warning("provider error: %s", e)
        return _error(503, "provider_error", str(e))

    @app.exception_handler(Exception)
    async def _unexpected(_: Request, e: Exception):
        log.exception("unhandled error")
        return _error(500, "internal_error", "Something went wrong. Check the server logs.")
