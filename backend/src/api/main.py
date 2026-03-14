from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.config import settings
from src.api.auth import router as auth_router
from src.api.cars import router as cars_router


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Enterprise Async API (Car Ads Platform)",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], #["https://yourdomain.com"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# Подключение роутеров (Маршрутизация)
# ==========================================
app.include_router(auth_router, prefix="/api/v1")
app.include_router(cars_router, prefix="/api/v1")

@app.get("/api/health", tags=["System"])
async def health_check() -> dict[str, str]:
    """Эндпоинт для проверки жизнеспособности контейнера."""
    return {"status": "ok", "version": settings.VERSION}