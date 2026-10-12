
import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from sqlalchemy.exc import SQLAlchemyError

log = logging.getLogger("errors")


class AppError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        status: int = 400,
    ):
        self.code = code
        self.message = message
        self.status = status


def _body(
    code: str,
    message: str,
    request: Request,
    details=None,
):
    return {
        "error": {
            "code": code,
            "message": message,
            "request_id": getattr(
                request.state, "request_id", None
            ),
            "details": details,
        }
    }


def register_handlers(app: FastAPI) -> None:
    
    @app.exception_handler(SQLAlchemyError)
    async def db_error(
        request: Request,
        exc: SQLAlchemyError,
    ):
        log.error(
            "database error: %s",
            type(exc).__name__,
        )

        return JSONResponse(
            _body(
                "database_unavailable",
                "Database is unavailable, try again shortly",
                request,
            ),
            status_code=503,
        )

    
    @app.exception_handler(AppError)
    async def app_error(
        request: Request,
        exc: AppError,
    ):
        return JSONResponse(
            _body(exc.code, exc.message, request),
            status_code=exc.status,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error(
        request: Request,
        exc: RequestValidationError,
    ):
        return JSONResponse(
            _body(
                "validation_error",
                "Invalid request",
                request,
                exc.errors(),
            ),
            status_code=422,
        )

    @app.exception_handler(Exception)
    async def unhandled(
        request: Request,
        exc: Exception,
    ):
        log.exception("unhandled error")

        return JSONResponse(
            _body(
                "internal_error",
                "Something went wrong",
                request,
            ),
            status_code=500,
        )
