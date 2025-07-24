# Используем официальный slim-образ Python 3.13
FROM python:3.13-slim-bookworm

# Рабочая директория
WORKDIR /app

RUN pip install poetry==1.8.4

# Копируем зависимости
COPY pyproject.toml poetry.lock ./

# Устанавливаем системные зависимости
RUN poetry config virtualenvs.create false && \
    poetry install --no-root --only main

# Копируем код
COPY . .


