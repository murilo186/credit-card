from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import DomainError
from app.core.logging import configure_application_logger, log_event

logger = configure_application_logger("app.errors", "INFO")


def error_response(
    status_code: int,
    code: str,
    message: str,
    details: dict[str, object] | None = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "details": details or {},
            }
        },
    )


def register_error_handlers(app: FastAPI) -> None:
    """Register centralized, non-sensitive API error responses."""

    @app.exception_handler(DomainError)
    async def handle_domain_error(request: Request, error: DomainError) -> JSONResponse:
        request.state.error_code = error.code
        return error_response(
            error.status_code,
            error.code,
            error.message,
            error.details,
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request,
        error: RequestValidationError,
    ) -> JSONResponse:
        del error
        request.state.error_code = "VALIDATION_ERROR"
        return error_response(
            422,
            "VALIDATION_ERROR",
            "Dados da requisição são inválidos.",
        )

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_error(
        request: Request,
        error: StarletteHTTPException,
    ) -> JSONResponse:
        codes = {
            400: ("BAD_REQUEST", "A requisição é inválida."),
            404: ("NOT_FOUND", "Recurso não encontrado."),
            409: ("CONFLICT", "A requisição entrou em conflito com o estado atual."),
        }
        code, message = codes.get(
            error.status_code,
            ("HTTP_ERROR", "Não foi possível processar a requisição."),
        )
        request.state.error_code = code
        return error_response(error.status_code, code, message)

    @app.exception_handler(Exception)
    async def handle_unexpected_error(
        request: Request,
        error: Exception,
    ) -> JSONResponse:
        del error
        request.state.error_code = "INTERNAL_ERROR"
        log_event(logger, "internal_server_error", path=request.url.path)
        return error_response(
            500,
            "INTERNAL_ERROR",
            "Ocorreu um erro interno.",
        )
