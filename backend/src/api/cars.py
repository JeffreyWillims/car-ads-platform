# backend/src/api/cars.py
from typing import Annotated, List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.security import get_current_user
from src.models.user import User
from src.repositories.car import CarRepository
from src.schemas.car import CarRead

router = APIRouter(tags=["Cars"])

@router.get(
    "/cars", 
    response_model=List[CarRead],
    summary="Получить список автомобилей (Защищено)"
)
async def get_cars_list(
    # Защита роута. Если токен невалиден, функция даже не начнет выполняться.
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(20, ge=1, le=100, description="Количество авто на странице"),
    offset: int = Query(0, ge=0, description="Смещение")
):
    """
    Возвращает список автомобилей с пагинацией.
    Требует JWT Token в заголовке Authorization.
    """
    repo = CarRepository(session)
    cars = await repo.get_all(limit=limit, offset=offset)
    return cars