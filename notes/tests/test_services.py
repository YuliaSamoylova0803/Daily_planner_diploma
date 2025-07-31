from unittest import mock

import requests
from django.core.exceptions import ValidationError

from notes import services
from unittest.mock import Mock, patch, MagicMock
from docx import Document
import pytest

from notes.models import Note
from notes.services import BaseDocumentGenerator, DefectStatementGenerator, DocumentService, TelegramNotificationService
from datetime import datetime
from io import BytesIO

# Тесты базового класса
def test_base_document_generator_init(mock_note):
    """Проверка инициализации базового генератора"""
    with pytest.raises(NotImplementedError):
        generator = BaseDocumentGenerator(mock_note)


def test_base_generate_method(mock_note):
    """Проверка, что generate вызывает NotImplementedError"""

    class TestGenerator(BaseDocumentGenerator):
        def validate_note_type(self):
            pass

        def _build_document_structure(self):
            pass

    generator = TestGenerator(mock_note)
    assert isinstance(generator.generate(), BytesIO)


# Тесты для DefectStatementGenerator
def test_defect_statement_validate_correct_type(mock_note):
    """Проверка валидации правильного типа заметки"""
    generator = DefectStatementGenerator(mock_note)
    generator.validate_note_type()  # Не должно вызывать ошибку

def test_defect_statement_validate_wrong_type():
    """Проверка валидации неправильного типа заметки"""
    wrong_note = Mock()
    wrong_note.note_type = "other_type"
    with pytest.raises(ValueError, match="только для дефектных ведомостей"):
        DefectStatementGenerator(wrong_note)

# Тесты для TelegramNotificationService
# notes/tests/test_services.py

def test_send_notification_no_credentials():
    """Тест проверки отсутствия credentials"""
    service = TelegramNotificationService(token=None, chat_id=None)
    assert service.send_notification(Mock()) is False


def test_send_notification_success(mocker):
    """Тест успешной отправки уведомления"""
    # Мокаем requests.post
    mock_post = mocker.patch('requests.post', return_value=Mock(status_code=200))

    service = TelegramNotificationService(token="test_token", chat_id="test_chat")
    mock_note = Mock()
    mock_note.note_type = 'test'
    mock_note.title = 'Test'
    mock_note.content = 'Test content'
    mock_note.object_name = ''
    mock_note.address = ''

    assert service.send_notification(mock_note) is True
    mock_post.assert_called_once()


def test_send_document_success(mocker):
    """Тест успешной отправки документа"""
    # Мокаем зависимости
    mock_post = mocker.patch('requests.post', return_value=Mock(status_code=200))
    mock_generator = mocker.patch('notes.services.DefectStatementGenerator')
    mock_generator.return_value.generate.return_value = BytesIO(b"test")

    service = TelegramNotificationService(token="test_token", chat_id="test_chat")
    mock_note = Mock()
    mock_note.note_type = 'defect_statement'
    mock_note.title = 'Test'
    mock_note.content = 'Test content'
    mock_note.object_name = ''
    mock_note.address = ''

    assert service.send_notification(mock_note) is True
    mock_post.assert_called_once()


# Интеграционные тесты
def test_full_flow(mock_note2, mocker):
    # Мокируем запросы к Telegram API
    mock_post = mocker.patch('requests.post')
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {'ok': True}

    # Мокируем работу с файлами
    mocker.patch('os.makedirs')
    mocker.patch('os.path.exists', return_value=True)

    # 1. Тестируем генерацию документа
    doc_buffer = DefectStatementGenerator(mock_note2).generate()
    assert doc_buffer is not None

    # 2. Тестируем отправку документа
    service = TelegramNotificationService(token="test_token", chat_id="test_chat")

    # Подготавливаем текст сообщения
    text = (
        "*Дефектная ведомость*\n"
        "*Заголовок:* Тестовая дефектная ведомость\n"
        "*Содержание:* Тестовое содержание\n"
        "*Объект:* Тестовый объект\n"
        "*Адрес:* Тестовый адрес"
    )

    # Мокируем DefectStatementGenerator, чтобы он не вызывался повторно
    mock_generator = mocker.patch('notes.services.DefectStatementGenerator')
    mock_generator.return_value.generate.return_value = doc_buffer

    # Вызываем метод с правильными аргументами
    result = service._send_document(mock_note2, "test_chat", text)

    assert result is True
    mock_post.assert_called_once()


# Для обработки ошибок (строки 48-50):
def test_generate_exception_handling(mocker):
    """Тест обработки исключений при генерации документа"""
    mock_note = MagicMock()
    mock_note.note_type = "defect_statement"

    # Мокируем ошибку при создании документа
    mocker.patch.object(DefectStatementGenerator, '_build_document_structure', side_effect=Exception("Test error"))

    with pytest.raises(Exception):
        DefectStatementGenerator(mock_note).generate()


# Для TelegramService (строки 201-217):
def test_telegram_send_document_failure(mocker, mock_note2):
    """Тест неудачной отправки документа"""
    service = TelegramNotificationService(token="test", chat_id="test")

    # 1. Мокируем запрос к Telegram
    mock_post = mocker.patch('requests.post')
    mock_post.return_value.status_code = 500

    # 2. Мокируем генератор, чтобы возвращал BytesIO
    mock_generator = mocker.patch('notes.services.DefectStatementGenerator')
    mock_generator.return_value.generate.return_value = BytesIO(b"test")

    # 3. Вызываем метод с МОКНУТОЙ заметкой (mock_note2)
    result = service._send_document(mock_note2, "chat_id", "Test message")

    assert result is False


def test_send_notification_document_failure(mocker, mock_note2):
    service = TelegramNotificationService(token="test", chat_id="test")
    mocker.patch('requests.post', return_value=MagicMock(status_code=500))

    result = service.send_notification(mock_note2)
    assert result is False


import pytest
from notes.services import DefectStatementGenerator
from notes.models import Note
from django.core.exceptions import ValidationError
from unittest.mock import MagicMock


@pytest.fixture
def defect_note():
    note = MagicMock(spec=Note)
    note.note_type = 'defect_statement'  # Исправлено на правильный тип
    return note


@pytest.mark.parametrize(
    "note_type, should_raise",
    [
        ("defect_statement", False),
        ("defect", True),
        ("other_type", True),
        ("", True),
        (None, True),
    ],
)
def test_defect_type_validation(note_type, should_raise):
    note = MagicMock()
    note.note_type = note_type

    if should_raise:
        with pytest.raises(ValueError, match="только для дефектных ведомостей"):
            DefectStatementGenerator(note)
    else:
        # Не должно вызывать исключение
        generator = DefectStatementGenerator(note)
        assert generator.note == note


def test_document_structure(defect_note):
    generator = DefectStatementGenerator(defect_note)

    # Мокируем методы, чтобы проверить их вызовы
    with patch.object(generator, '_add_header') as mock_header, \
            patch.object(generator, '_add_main_info') as mock_main, \
            patch.object(generator, '_create_defects_table') as mock_table, \
            patch.object(generator, '_add_signatures_section') as mock_sign:
        generator._build_document_structure()

        mock_header.assert_called_once()
        mock_main.assert_called_once()
        mock_table.assert_called_once()
        mock_sign.assert_called_once()


def test_add_defect_image():
    note = MagicMock()
    note.note_type = 'defect_statement'
    generator = DefectStatementGenerator(note)

    # Тестирование метода _add_defect_image
    cell = MagicMock()
    defect = MagicMock()
    defect.images.exists.return_value = True
    image = MagicMock()
    defect.images.first.return_value = image
    image.image.path = "/test/path.jpg"

    with patch('docx.shared.Cm'), patch('docx.text.run.Run.add_picture'):
        generator._add_defect_image(cell, defect)
        cell.paragraphs[0].add_run().add_picture.assert_called_once()


def test_generate_document(defect_note):
    generator = DefectStatementGenerator(defect_note)
    result = generator.generate()

    assert isinstance(result, BytesIO)
    assert len(result.getvalue()) > 0  # Документ не пустой


def test_base_generator_error_handling(mock_note):
    """Тест обработки ошибок в базовом генераторе"""

    class TestGenerator(BaseDocumentGenerator):
        def validate_note_type(self):
            pass

        def _build_document_structure(self):
            raise IOError("Test error")

    generator = TestGenerator(mock_note)
    with pytest.raises(Exception):
        generator.generate()


def test_telegram_send_message_failure(mocker):
    """Тест ошибки при отправке текстового сообщения"""
    mock_post = mocker.patch('requests.post')
    mock_post.side_effect = requests.exceptions.RequestException("Test error")

    service = TelegramNotificationService(token="test", chat_id="test")
    assert service._send_text_message("chat_id", "test") is False


def test_telegram_prepare_message_empty_note():
    """Тест подготовки сообщения с пустой заметкой"""
    service = TelegramNotificationService()
    note = MagicMock()
    note.get_note_type_display.return_value = "Test"
    note.title = ""
    note.content = ""
    note.object_name = ""
    note.address = None

    message = service._prepare_message(note)
    assert "*Test*" in message
    assert "*Заголовок:* " in message


def test_add_defect_image_no_image(mocker):
    """Тест добавления дефекта без изображения"""
    note = MagicMock()
    note.note_type = 'defect_statement'
    generator = DefectStatementGenerator(note)

    cell = MagicMock()
    defect = MagicMock()
    defect.images.exists.return_value = False

    generator._add_defect_image(cell, defect)
    assert not cell.paragraphs[0].add_run.called


def test_save_document_io_error(mocker, mock_note):
    """Тест ошибки при сохранении документа"""
    # Правильно настраиваем mock для defects
    mock_defects = MagicMock()
    mock_defects.all.return_value.order_by.return_value = []  # Эмулируем QuerySet

    # Устанавливаем defects в mock_note
    mock_note.defects = mock_defects

    # Мокируем os.makedirs чтобы вызвать ошибку
    mocker.patch('os.makedirs', side_effect=OSError("Test error"))

    # Мокируем генератор, чтобы не создавать реальный документ
    mock_generator = MagicMock()
    mock_generator.generate.return_value = BytesIO(b"test")
    mocker.patch('notes.services.DefectStatementGenerator', return_value=mock_generator)

    with pytest.raises(IOError):
        DocumentService.save_defect_statement(mock_note)