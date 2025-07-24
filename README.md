## Проект "Веб-приложение Daily_planner - это многофункциональное веб-приложение для:"

## Цели проекта
+ 📔 Ведения личного дневника
+ 🛠️ Учета рабочих задач и дефектов
+ 📝 Формирования дефектных ведомостей
+ 📤 Экспорта отчетов в Word
+ 📨 Отправки уведомлений в Telegram

## Используются следующие зависимости:

- poetry add django
- poetry init
- pathlib
- poetry add --group lint flake8 black mypy isort 
- ipython
- Pillow
- python-dotenv
- psycopg2-binary
- redis
- python-docx
- openpyxl
- python-docx

### Версии и зависимости:

[tool.poetry]
name = "daily-planner"
version = "0.1.0"
description = ""
authors = ["Юлия Самойлова <Ulia629736@yandex.ru>"]
readme = "README.md"

[tool.poetry.dependencies]
python = "^3.13"
django = "^5.2.4"
ipython = "^9.4.0"
pillow = "^11.3.0"
python-dotenv = "^1.1.1"
psycopg2-binary = "^2.9.10"
redis = "^6.2.0"
openpyxl = "^3.1.5"
docx = "^0.2.4"
python-docx = "^1.2.0"
markdown = "^3.8.2"
requests = "^2.32.4"


[tool.poetry.group.lint.dependencies]
flake8 = "^7.3.0"
black = "^25.1.0"
mypy = "^1.16.1"
isort = "^6.0.1"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"


## Основные возможности
### Личный дневник
- ✍️ Создание личных записей с настроением
-🔒 Возможность пометить запись как приватную
- 🔍 Поиск по всем записям
- 🗑️ Управление записями (редактирование/удаление)

### Рабочий модуль
- 🚧 Создание дефектов с:
- 📷 Прикреплением фотографий
-📝 Подробным описанием
- ⏱️ Сроком устранения
- 📋 Формирование дефектных ведомостей
- 📄 Экспорт ведомостей в Word
- 📨 Отправка уведомлений в Telegram

## 🛠 Технологический стек
+ Backend: Django 5.2.4
+ Database: PostgreSQL
+ Frontend: Bootstrap 5 + Django Templates

### Дополнительные библиотеки:

- python-docx - работа с Word
- python-telegram-bot - интеграция с Telegram
- Pillow - обработка изображений
- openpyxl - работа с Excel (резервный экспорт)
### Инструменты:
- Docker для контейнеризации
- Poetry для управления зависимостями


### 📂 Структура проекта

daily-planner/
├── config/               # Настройки проекта
├── notes/                 # Основное приложение
│   ├── migrations/       # Миграции БД
│   ├── templates/        # Шаблоны
│   │   ├── notes/        # Шаблоны записей
│   │   └── base.html     # Базовый шаблон
│   ├── __init__.py
│   ├── admin.py          # Админ-панель
│   ├── apps.py
│   ├── forms.py          # Все формы
│   ├── models.py         # Модели данных
│   ├── services.py       # Бизнес-логика
│   ├── tests.py          # Тесты
│   ├── urls.py           # URL-маршруты
│   ├── views.py          # Представления
│   └── utils/            # Вспомогательные модули
├── media/                # Загружаемые файлы (изображения)
├── static/               # Статические файлы (CSS, JS)
├── users/                # Приложение пользователей
├── .env                  # Переменные окружения
├── .env.sample           # Шаблон .env
├── .gitignore
├── manage.py             # Точка входа Django
├── poetry.lock           # Зависимости Poetry
├── pyproject.toml        # Конфигурация Poetry
└── README.md             # Этот файл

## 🧩 Основные модели
+ Note (Запись)

class Note(models.Model):
    NOTE_TYPE_CHOICES = [
        ("personal", "Личная запись"),
        ("work", "Рабочая запись"),
        ("defect", "Дефект"),
        ("statement", "Ведомость"),
    ]
+ DefectImage (Изображение дефекта)
+ DefectStatement (Дефектная ведомость)

🛠 Установка и запуск
1. Установка зависимостей
bash
poetry install
2. Настройка окружения
Создайте .env файл на основе .env.sample:

bash
cp .env.sample .env
Заполните необходимые переменные (БД, Telegram токен и др.)

3. Запуск с Docker
bash
docker-compose up --build
4. Миграции и суперпользователь
bash
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser

## 📧 Контакты
Автор: Юлия Самойлова
Email: Ulia629736@yandex.ru