# backend/src/api/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse

from src.core.config import settings
from src.api.auth import router as auth_router
# from src.api.cars import router as cars_router # Подключим позже

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Enterprise Async API (Car Ads Platform)",
    default_response_class=ORJSONResponse, # O(N) сериализация на Rust
    docs_url="/api/docs",
    openapi_url="/api/openapi.json"
)

# CORS конфигурация (В проде allow_origins нужно ограничить доменом фронтенда!)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Регистрация роутеров
app.include_router(auth_router, prefix="/api/v1")
# app.include_router(cars_router, prefix="/api/v1")

@app.get("/api/health", tags=["System"])
async def health_check() -> dict[str, str]:
    """Liveness probe для Docker Healthcheck"""
    return {"status": "ok", "version": settings.VERSION}