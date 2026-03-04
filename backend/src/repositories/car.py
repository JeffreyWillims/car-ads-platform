# backend/src/repositories/car.py
from typing import Any, Sequence
from sqlalchemy import select, desc, update, func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.car import Car

class CarRepository:
    """
    Data Access Layer for Car entity.
    """
    def __init__(self, session: AsyncSession):
        self.session = session

    # ИСПРАВЛЕНО: upsert_bulk -> bulk_upsert
    async def bulk_upsert(self, cars_data: list[dict[str, Any]]) -> None:
        """
        Массовое сохранение машин (O(log N)).
        """
        if not cars_data:
            return

        stmt = insert(Car).values(cars_data)

        # Логика обновления при совпадении ссылки
        upsert_stmt = stmt.on_conflict_do_update(
            index_elements=['link'],
            set_={
                "price": stmt.excluded.price,
                "model": stmt.excluded.model,
                "year": stmt.excluded.year,
                "color": stmt.excluded.color,
                "mileage": stmt.excluded.mileage,
                "image_url": stmt.excluded.image_url,
                "updated_at": stmt.excluded.updated_at,
            }
        )

        await self.session.execute(upsert_stmt)
        await self.session.commit()

    async def get_all(self, limit: int = 100, offset: int = 0) -> Sequence[Car]:
        # Сортируем по updated_at, чтобы свежеспаршенные (или обновленные) были сверху
        query = select(Car).order_by(desc(Car.updated_at)).limit(limit).offset(offset)
        result = await self.session.execute(query)
        return result.scalars().all()

    # --- Методы для AI (Оставляем как есть) ---
    async def get_cars_without_description(self, batch_size: int = 5) -> Sequence[Car]:
        query = (
            select(Car)
            .where(Car.ai_description.is_(None))
            .limit(batch_size)
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    async def update_description(self, car_id: int, description: str) -> None:
        stmt = (
            update(Car)
            .where(Car.id == car_id)
            .values(ai_description=description)
        )
        await self.session.execute(stmt)
        await self.session.commit()

    async def search_cars(self, filters: Any, limit: int = 5) -> Sequence[Car]:
        """
        O(N) Динамическая фильтрация автомобилей на основе AI-запроса.
        """
        query = select(Car)

        if filters.brand:
            query = query.where(Car.brand.ilike(f"%{filters.brand}%"))
        if filters.model:
            query = query.where(Car.model.ilike(f"%{filters.model}%"))
        if filters.min_year:
            query = query.where(Car.year >= filters.min_year)
        if filters.max_price:
            query = query.where(Car.price <= filters.max_price)
        if filters.color:
            query = query.where(Car.color.ilike(f"%{filters.color}%"))

        query = query.order_by(desc(Car.created_at)).limit(limit)
        result = await self.session.execute(query)
        return result.scalars().all()