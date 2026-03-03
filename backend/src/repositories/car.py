from typing import Any, Sequence
from sqlalchemy import select, desc, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.car import Car

class CarRepository:
    """
    Data Access Layer for Car entity.
    """
    def __init__(self, session: AsyncSession):
        self.session = session

    async def upsert_bulk(self, cars_data: list[dict[str, Any]]) -> int:
        if not cars_data:
            return 0

        # ВАЖНО: cars_data не должен содержать ключей, которых нет в модели Car!
        stmt = insert(Car).values(cars_data)

        update_dict = {
            "price": stmt.excluded.price,
            "model": stmt.excluded.model, # Обновляем модель
            "year": stmt.excluded.year,
            "updated_at": stmt.excluded.updated_at,
        }

        upsert_stmt = stmt.on_conflict_do_update(
            index_elements=['link'],
            set_=update_dict
        )

        result = await self.session.execute(upsert_stmt)
        await self.session.commit()
        return result.rowcount

    async def get_all(self, limit: int = 100, offset: int = 0) -> Sequence[Car]:
        query = select(Car).order_by(desc(Car.created_at)).limit(limit).offset(offset)
        result = await self.session.execute(query)
        return result.scalars().all()

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