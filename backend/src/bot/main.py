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

# Инициализация логирования и бота
logging.basicConfig(level=logging.INFO, stream=sys.stdout)

token = settings.BOT_TOKEN.get_secret_value()
bot = Bot(token=token)
dp = Dispatcher()


@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer(
        "Привет! Я AI-агент 🤖 по подбору авто из Японии.\n"
        "Напиши мне запрос в свободной форме. Например:\n"
        "<i>'Найди белую Хонду не старше 2020 года'</i>",
        parse_mode=ParseMode.HTML
    )


@dp.message(F.text)
async def handle_text(message: types.Message):
    # Показываем статус "печатает..."
    await bot.send_chat_action(message.chat.id, "typing")
    status_msg = await message.answer("🤔 Нейросеть анализирует запрос...")

    # 1. AI парсит текст
    filters = await analyze_user_query(message.text)

    if not filters:
        await status_msg.edit_text("Не смог распознать параметры. Попробуй уточнить марку или цвет.")
        return

    # 2. Идем в базу данных
    async with AsyncSessionLocal() as session:
        repo = CarRepository(session)
        # Берем только 5 машин, чтобы сообщение не превысило лимит Telegram
        cars = await repo.search_cars(filters, limit=5)

    if not cars:
        # Собираем строку фильтров
        filters_desc =[
            f"Марка: {filters.brand}" if filters.brand else None,
            f"Модель: {filters.model}" if filters.model else None,
            f"От {filters.min_year} года" if filters.min_year else None,
            f"Цвет: {filters.color}" if filters.color else None,
        ]
        filter_str = ", ".join(f for f in filters_desc if f) or "любые параметры"

        await status_msg.edit_text(f"По запросу (<b>{filter_str}</b>) ничего не найдено в базе 😔", parse_mode=ParseMode.HTML)
        return

    # 3. Рендеринг ответа
    response_text = "<b>Вот что я нашел для тебя:</b>\n\n"

    for car in cars:
        # Безопасное извлечение AI описания с ограничением по длине (100 символов)
        desc_text = ""
        if getattr(car, "ai_description", None):
            desc_text = f"💡 <i>{car.ai_description[:100]}...</i>\n"

        # Форматирование чисел для красоты
        price_formatted = f"¥ {car.price:,}"
        mileage_text = f"🛣 {car.mileage:,} км | " if car.mileage else ""

        response_text += (
            f"🚗 <b>{car.brand} {car.model}</b>\n"
            f"📅 Год: {car.year} | {mileage_text}💰 {price_formatted}\n"
            f"{desc_text}"
            f"🔗 <a href='{car.link}'>Смотреть на сайте</a>\n\n"
        )

    await status_msg.edit_text(response_text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)


async def main():
    # Удаляем вебхуки и старые апдейты, чтобы бот не спамил старыми сообщениями при старте
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())