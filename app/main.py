from fastapi import FastAPI

from app.api.routes import (
    card_router,
    customer_router,
    health_router,
    transaction_router,
)
from app.core.config import settings

app = FastAPI(title=settings.app_name, version="1.0.0")
app.include_router(health_router)
app.include_router(customer_router)
app.include_router(card_router)
app.include_router(transaction_router)
