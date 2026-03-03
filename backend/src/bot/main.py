import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.enums import ParseMode

from src.core.config import settings
from src.core.database import AsyncSessionLocal
from src.repositories.car import CarRepository
from src.bot.ai_service import analyze_user_query

# Настройка логирования
logging.basicConfig(level=logging.INFO, stream=sys.stdout)

# Инициализация бота
# Если в config.py BOT_TOKEN это str, используем его напрямую.
# Если это SecretStr, используем .get_secret_value().
token = settings.BOT_TOKEN.get_secret_value() if hasattr(settings.BOT_TOKEN, "get_secret_value") else settings.BOT_TOKEN
bot = Bot(token=token)
dp = Dispatcher()


@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer(
        "Привет! Я AI-бот 🤖. Напиши, какую машину ты ищешь (например: 'Найди красную Мазду до 2020 года')."
    )


@dp.message(F.text)
async def handle_text(message: types.Message):
    status_msg = await message.answer("🤔 Анализирую твой запрос через нейросеть...")

    # 1. AI парсит текст пользователя в структурированный Pydantic объект
    filters = await analyze_user_query(message.text)

    if not filters:
        await status_msg.edit_text("Не смог понять параметры поиска. Попробуй иначе.")
        return

    # 2. Обращаемся к слою данных (Clean Architecture)
    async with AsyncSessionLocal() as session:
        repo = CarRepository(session)
        cars = await repo.search_cars(filters)

    if not cars:
        # Собираем красивую строку фильтров для ответа
        filters_desc = []
        if filters.brand: filters_desc.append(f"Марка: {filters.brand}")
        if filters.model: filters_desc.append(f"Модель: {filters.model}")
        if filters.min_year: filters_desc.append(f"От {filters.min_year} года")
        if filters.max_price: filters_desc.append(f"До {filters.max_price} руб")
        if filters.color: filters_desc.append(f"Цвет: {filters.color}")

        filter_str = ", ".join(filters_desc) if filters_desc else "любые параметры"

        await status_msg.edit_text(
            f"По запросу ({filter_str}) ничего не найдено в базе 😔\nПопробуй поискать другую машину.")
        return

    # 3. Формируем ответ
    response_text = "Вот что я нашел в нашей базе:\n\n"

    # ИСПРАВЛЕНО: Цикл for должен быть на том же уровне отступа, что и response_text
    for car in cars:
        # ПРОВЕРКА НАЛИЧИЯ ПОЛЯ ai_description (Safeguard)
        desc_text = ""
        if hasattr(car, "ai_description") and car.ai_description:
            desc_text = f"💡 <i>{car.ai_description[:100]}...</i>\n"

        response_text += (
            f"🚗 <b>{car.brand} {car.model}</b>\n"
            f"📅 Год: {car.year} | 💰 Цена: {car.price} JPY\n"
            f"{desc_text}"
            f"🔗 <a href='{car.link}'>Смотреть на сайте</a>\n\n"
        )

    await status_msg.edit_text(response_text, parse_mode=ParseMode.HTML)


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())