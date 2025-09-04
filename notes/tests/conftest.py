import pytest
from unittest.mock import Mock
from django.utils import timezone
from datetime import datetime

@pytest.fixture
def mock_note():
    note = Mock()
    note.note_type = "defect_statement"
    note.statement_number = "123"
    note.address = "ул. Примерная, 1"
    note.object_name = "Тестовый объект"
    note.defects = Mock()
    note.defects.all.return_value = []
    note.approved_by = "Иванов И.И."
    note.approval_date = datetime(2025, 1, 1)
    return note

@pytest.fixture
def mock_defect_with_image():
    defect = Mock()
    defect.id = 1
    defect.content = "Трещина в стене"
    defect.title = "Заделать трещину"
    defect.images = Mock()
    image_mock = Mock()
    image_mock.image.path = "/fake/path/to/image.jpg"
    defect.images.exists.return_value = True
    defect.images.first.return_value = image_mock
    return defect


@pytest.fixture
def mock_timezone(monkeypatch):
    """Фикстура для корректного мока timezone.now()"""
    from django.utils import timezone
    mock_now = datetime(2023, 1, 1, 12, 0)  # Фиксированная дата для тестов
    monkeypatch.setattr(timezone, 'now', lambda: mock_now)


from django.db.models.query import QuerySet
from unittest.mock import MagicMock


@pytest.fixture
def mock_note2():
    note = MagicMock()
    note.note_type = "defect_statement"
    note.statement_number = "123"
    note.address = "Тестовый адрес"
    note.object_name = "Тестовый объект"
    note.title = "Тестовая дефектная ведомость"
    note.content = "Тестовое содержание"
    note.approved_by = "Иванов И.И."
    note.approval_date = timezone.now()

    # Моки для дефектов
    defect1 = MagicMock()
    defect1.content = "Дефект 1"
    defect1.title = "Ремонт 1"
    defect1.created_at = timezone.now()
    defect1.images = MagicMock()
    defect1.images.exists.return_value = False

    defect2 = MagicMock()
    defect2.content = "Дефект 2"
    defect2.title = "Ремонт 2"
    defect2.created_at = timezone.now()
    defect2.images = MagicMock()
    defect2.images.exists.return_value = False

    defects_mock = MagicMock(spec=QuerySet)
    defects_mock.all.return_value.order_by.return_value = [defect1, defect2]
    note.defects = defects_mock

    return note
