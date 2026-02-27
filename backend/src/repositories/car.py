from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import select

from src.models.car import Car

class CarRepository:
    """
    Паттерн Repository.
    Изолирует сложные SQL-запросы от бизнес-логики (FastAPI/Celery).
    """
    def __init__(self, session: AsyncSession):
        self.session = session

    async def bulk_upsert(self, cars_data: list[dict]) -> None:
        """
        Выполняет массовый Upsert (Добавление или Обновление).
        Time Complexity: O(K * log N), где K - количество новых авто, N - размер БД.
        """
        if not cars_data:
            return

        # 1. Формируем базовый INSERT
        stmt = insert(Car).values(cars_data)

        # 2. Исключаем поля, которые не нужно обновлять при конфликте (например, id и created_at)
        # stmt.excluded содержит данные, которые мы пытались вставить
        update_dict = {
            "price": stmt.excluded.price,
            "color": stmt.excluded.color,
            "updated_at": stmt.excluded.updated_at,
            # Можно добавить другие поля, если скрапер может уточнить их позже
        }

        # 3. Настраиваем логику ON CONFLICT (по уникальному полю 'link')
        upsert_stmt = stmt.on_conflict_do_update(
            index_elements=['link'], # Наш Unique Constraint
            set_=update_dict
        )

        # 4. Выполняем батч
        await self.session.execute(upsert_stmt)
        await self.session.commit()

    async def get_all(self, limit: int = 100, offset: int = 0) -> list[Car]:
        """Получение списка машин для API с пагинацией"""
        query = select(Car).limit(limit).offset(offset).order_by(Car.created_at.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())