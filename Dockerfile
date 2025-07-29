# Используем официальный slim-образ Python 3.13
FROM python:3.13-slim-bookworm

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Рабочая директория
WORKDIR /app

RUN pip install poetry==1.8.4

# Копируем зависимости
COPY pyproject.toml poetry.lock ./

# Устанавливаем системные зависимости
RUN poetry config virtualenvs.create false && \
    poetry install --only main --no-interaction --no-ansi

# Копируем код
COPY . .

# После COPY . .
RUN mkdir -p /app/static_dev /app/static /app/media

# Сборка статики для production
ARG DJANGO_ENV=development
RUN if [ "$DJANGO_ENV" = "production" ]; then \
        python manage.py collectstatic --noinput; \
    fi

# Healthcheck
HEALTHCHECK --interval=30s --timeout=3s \
    CMD curl -f http://localhost:8000/health/ || exit 1

# Команда по умолчанию (переопределяется в docker-compose)
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "config.wsgi:application"]