from celery import Celery
from src.core.config import settings
from celery.schedules import crontab

# Инициализация приложения
# broker: Куда кидать задачи (Redis)
# backend: Куда сохранять результаты (Redis)
celery_app = Celery(
    "worker",
    broker=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0",
    backend=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0",
)

# Enterprise-настройки для надежности
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,

    # ACKS_LATE: Задача считается выполненной только ПОСЛЕ завершения.
    # Если воркер упадет во время работы, задача вернется в очередь.
    task_acks_late=True,

    # Ограничение памяти (защита от утечек)
    worker_max_tasks_per_child=1000,
)

# Автоматический поиск задач в папке worker
celery_app.autodiscover_tasks(["src.worker"])

# Настройка периодических задач
celery_app.conf.beat_schedule = {
    "scrape-every-10-mins": {
        "task": "scrape_cars_task", # Имя, которое мы дали в @shared_task
        "schedule": crontab(minute="*/10"), # Каждые 10 минут
    },
}