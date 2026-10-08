import time
import uuid

from fastapi import FastAPI, Request

from app.api.routes import (
    card_router,
    customer_router,
    health_router,
    transaction_router,
)
from app.core.config import settings
from app.core.error_handlers import error_response, register_error_handlers
from app.core.logging import configure_application_logger, log_event

app = FastAPI(title=settings.app_name, version="1.0.0")
logger = configure_application_logger("app.requests", settings.log_level)


@app.middleware("http")
async def request_context_and_logging(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    started_at = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        request.state.error_code = "INTERNAL_ERROR"
        log_event(logger, "internal_server_error", path=request.url.path)
        response = error_response(
            500,
            "INTERNAL_ERROR",
            "Ocorreu um erro interno.",
        )
    response.headers["X-Request-ID"] = request_id
    log_event(
        logger,
        "request_completed",
        request_id=request_id,
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration_ms=round((time.perf_counter() - started_at) * 1000, 2),
        error_code=getattr(request.state, "error_code", None),
    )
    return response


register_error_handlers(app)
app.include_router(health_router)
app.include_router(customer_router)
app.include_router(card_router)
app.include_router(transaction_router)
