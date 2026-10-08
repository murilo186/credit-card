from fastapi import FastAPI

from app.api.routes.health import router as health_router
from app.core.config import settings

app = FastAPI(title=settings.app_name, version="1.0.0")
app.include_router(health_router)
