# ==========================================
# STAGE 1: Builder (Сборка зависимостей)
# ==========================================
FROM python:3.12-slim AS builder

# Аргументы сборки (можно переопределить через --build-arg)
ARG POETRY_VERSION=1.8.2

# Переменные окружения для сборки
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

# Установка системных зависимостей для сборки (компиляторы C)
# git - нужен, если есть зависимости из git-репозиториев
# build-essential, libpq-dev - для сборки драйверов БД (psycopg2)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Установка Poetry через pip (безопасно в изолированном build-слое)
RUN pip install "poetry==${POETRY_VERSION}"

WORKDIR /app

# 1. Сначала копируем только файлы зависимостей!
# Это позволяет Docker кэшировать слой с установленными пакетами.
# Если вы измените код, но не зависимости -> `poetry install` не будет выполняться заново.
COPY pyproject.toml poetry.lock* ./

# 2. Установка зависимостей (Production only)
# --no-root: не устанавливаем сам проект как пакет (код скопируем в runtime)
RUN poetry install --without dev --no-root && rm -rf ${POETRY_CACHE_DIR}

# ==========================================
# STAGE 2: Runtime (Финальный образ)
# ==========================================
FROM python:3.12-slim AS runtime

# Переменные для рантайма
ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    # Защита от CVE-2019-14697 (Stack overflow в musl)
    PYTHONDONTWRITEBYTECODE=1

# Установка рантайм-зависимостей (минимальный набор)
# curl - для Healthcheck
# libpq5 - для работы с PostgreSQL
# tini - правильный init-процесс для обработки сигналов (Ctrl+C, SIGTERM)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libpq5 \
    tini \
    && rm -rf /var/lib/apt/lists/*

# Создание непривилегированного пользователя
# UID 1000 - стандарт для Linux
RUN useradd -m -u 1000 appuser && \
    mkdir /app && \
    chown appuser:appuser /app

WORKDIR /app

# Копируем виртуальное окружение из Builder (Самый важный шаг)
COPY --from=builder --chown=appuser:appuser /app/.venv /app/.venv

# Копируем исходный код приложения
COPY --chown=appuser:appuser src ./src
# Если нужны скрипты миграций в корне (alembic.ini), раскомментируй:
COPY --chown=appuser:appuser alembic.ini .
COPY --chown=appuser:appuser src/migrations ./migrations

# Переключаемся на пользователя
USER appuser

# Healthcheck (Проверка жизни контейнера)
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Используем Tini как Entrypoint (гасит зомби-процессы)
ENTRYPOINT ["/usr/bin/tini", "--"]

# Команда запуска по умолчанию
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]