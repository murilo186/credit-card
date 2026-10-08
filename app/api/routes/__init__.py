"""API route modules."""

from app.api.routes.card import router as card_router
from app.api.routes.customer import router as customer_router
from app.api.routes.health import router as health_router

__all__ = ["card_router", "customer_router", "health_router"]
