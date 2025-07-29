import logging
import os
from io import BytesIO
from urllib.parse import quote
from typing import Optional

import requests
from django.conf import settings
from django.utils import timezone
from docx import Document
from docx.shared import Cm

logger = logging.getLogger(__name__)


class BaseDocumentGenerator:
    """Базовый класс для генерации документов"""

    def __init__(self, note):
        """
        Инициализация генератора документов

        Args:
            note: Объект заметки модели Note
        """
        self.note = note
        self.doc = Document()
        self.validate_note_type()

    def validate_note_type(self):
        """Проверка типа заметки (должен быть переопределен в дочерних классах)"""
        raise NotImplementedError("Метод validate_note_type должен быть реализован")

    def generate(self) -> BytesIO:
        """
        Генерация документа

        Returns:
            BytesIO: Байтовый поток с содержимым документа

        Raises:
            ValueError: Если передан объект неправильного типа
            IOError: При ошибках работы с файлами
        """
        try:
            self._build_document_structure()
            return self._save_to_buffer()
        except Exception as e:
            logger.error(f"Ошибка генерации документа: {str(e)}", exc_info=True)
            raise

    def _build_document_structure(self):
        """Построение структуры документа (должен быть переопределен)"""
        raise NotImplementedError("Метод _build_document_structure должен быть реализован")

    def _save_to_buffer(self) -> BytesIO:
        """Сохранение документа в буфер памяти"""
        buffer = BytesIO()
        self.doc.save(buffer)
        buffer.seek(0)
        return buffer


class DefectStatementGenerator(BaseDocumentGenerator):
    """
    Генератор дефектных ведомостей в формате DOCX

    Пример использования:
    >>> generator = DefectStatementGenerator(note)
    >>> doc_buffer = generator.generate()

    Attributes:
        note (Note): Объект заметки с типом 'defect_statement'
        doc (Document): Объект документа Word
    """

    def validate_note_type(self):
        """Проверка, что заметка является дефектной ведомостью"""
        if self.note.note_type != "defect_statement":
            raise ValueError("Эта функция предназначена только для дефектных ведомостей")

    def _build_document_structure(self):
        """Построение структуры дефектной ведомости"""
        self._add_header()
        self._add_main_info()
        self._create_defects_table()
        self._add_signatures_section()

    def _add_header(self):
        """Добавление заголовка документа"""
        self.doc.add_heading(f"Дефектная ведомость №{self.note.statement_number}", level=1)
        self.doc.add_paragraph(f"на текущий ремонт помещения (здания) {self.note.address}")

    def _add_main_info(self):
        """Добавление основной информации"""
        self.doc.add_paragraph(f"Наименование объекта: {self.note.object_name}")
        self.doc.add_paragraph(f"Адрес объекта: {self.note.address}")
        self.doc.add_paragraph(f'Дата составления: {timezone.now().strftime("%d.%m.%Y")}')

    def _create_defects_table(self):
        """Создание и заполнение таблицы дефектов"""
        table = self.doc.add_table(rows=1, cols=6)
        table.style = "Table Grid"

        # Настройка ширины колонок
        widths = (Cm(1.5), Cm(3.5), Cm(5), Cm(4), Cm(2), Cm(2.5))
        for i, width in enumerate(widths):
            table.columns[i].width = width

        # Заголовки таблицы
        headers = [
            "№ п/п", "Фото дефекта", "Обнаруженные дефекты",
            "Необходимые работы", "Объем", "Сроки"
        ]

        for i, header in enumerate(headers):
            cell = table.rows[0].cells[i]
            cell.text = header
            cell.paragraphs[0].runs[0].font.bold = True

        # Заполнение данными
        for i, defect in enumerate(self.note.defects.all().order_by("created_at"), start=1):
            row_cells = table.add_row().cells
            row_cells[0].text = str(i)
            row_cells[2].text = defect.content
            row_cells[3].text = defect.title
            self._add_defect_image(row_cells[1], defect)

    def _add_defect_to_table(self, table, defect, index):
        """Добавление строки с дефектом в таблицу"""
        row_cells = table.add_row().cells
        row_cells[0].text = str(index)
        row_cells[2].text = defect.content
        row_cells[3].text = defect.title
        self._add_defect_image(row_cells[1], defect)

    def _add_defect_image(self, cell, defect):
        """Добавление изображения дефекта в ячейку таблицы"""
        if defect.images.exists():
            try:
                image = defect.images.first()
                paragraph = cell.paragraphs[0]
                run = paragraph.add_run()
                run.add_picture(image.image.path, width=Cm(3), height=Cm(2))
            except Exception as e:
                logger.warning(f"Не удалось добавить изображение для дефекта {defect.id}: {str(e)}")
                cell.text = "Фото (ошибка загрузки)"

    def _add_signatures_section(self):
        """Добавление раздела с подписями"""
        self.doc.add_paragraph("\nСоставил: _________________________")
        if self.note.approved_by:
            self.doc.add_paragraph(f"\nУтверждаю: {self.note.approved_by}")
        if self.note.approval_date:
            self.doc.add_paragraph(f"Дата: {self.note.approval_date.strftime('%d.%m.%Y')}")


class DocumentService:
    """
    Сервис для работы с файлами документов

    Static Methods:
        save_defect_statement(note): Сохраняет ведомость в файл
        generate_defect_statement(note): Генерирует и возвращает файл
    """

    @staticmethod
    def save_defect_statement(note) -> str:
        """
        Сохранение дефектной ведомости в файл

        Args:
            note: Объект заметки модели Note

        Returns:
            str: Относительный путь к сохраненному файлу

        Raises:
            IOError: При ошибках записи файла
        """
        try:
            generator = DefectStatementGenerator(note)
            doc_buffer = generator.generate()

            filename = f"defect_statement_{note.id}_{timezone.now().strftime('%Y%m%d_%H%M')}.docx"
            filename = quote(filename)  # Экранирование специальных символов
            filepath = os.path.join(settings.MEDIA_ROOT, "generated_docs", filename)

            os.makedirs(os.path.dirname(filepath), exist_ok=True)

            with open(filepath, "wb") as f:
                f.write(doc_buffer.getvalue())

            return os.path.join("generated_docs", filename)
        except Exception as e:
            logger.error(f"Ошибка сохранения документа: {str(e)}", exc_info=True)
            raise


class TelegramNotificationService:
    """
    Сервис для отправки уведомлений в Telegram

    Требует настройки в settings.py:
    - TELEGRAM_TOKEN: токен бота
    - TELEGRAM_CHAT_ID: ID чата по умолчанию

    Пример использования:
    >>> service = TelegramNotificationService()
    >>> success = service.send_notification(note)
    """

    def __init__(self):
        self.token = getattr(settings, "TELEGRAM_TOKEN", "")
        self.chat_id = getattr(settings, "TELEGRAM_CHAT_ID", "")

        if not self.token or not self.chat_id:
            logger.warning("Telegram credentials не настроены в settings.py")

    def send_notification(self, note, chat_id: Optional[str] = None) -> bool:
        """
        Отправка уведомления в Telegram

        Args:
            note: Объект заметки модели Note
            chat_id: ID чата для отправки (если None, используется из настроек)

        Returns:
            bool: True если отправка успешна, False в случае ошибки
        """
        if not self._validate_credentials(chat_id):
            return False

        try:
            text = self._prepare_message(note)
            chat_id = chat_id or self.chat_id

            if note.note_type == "defect_statement":
                return self._send_document(note, chat_id, text)
            return self._send_text_message(chat_id, text)

        except Exception as e:
            logger.error(f"Ошибка отправки в Telegram: {str(e)}", exc_info=True)
            return False

    def _validate_credentials(self, chat_id: Optional[str]) -> bool:
        """Проверка наличия необходимых учетных данных"""
        if not self.token or not (chat_id or self.chat_id):
            logger.warning("Не настроены Telegram credentials")
            return False
        return True

    def _prepare_message(self, note) -> str:
        """Подготовка текста сообщения"""
        message = [
            f"*{note.get_note_type_display()}*",
            f"*Заголовок:* {note.title}",
            f"*Содержание:* {note.content}",
        ]

        if note.object_name:
            message.append(f"*Объект:* {note.object_name}")
        if note.address:
            message.append(f"*Адрес:* {note.address}")

        return "\n".join(message)

    def _send_document(self, note, chat_id: str, text: str) -> bool:
        """Отправка документа в Telegram"""
        try:
            generator = DefectStatementGenerator(note)
            doc_buffer = generator.generate()

            files = {"document": (f"defect_{note.id}.docx", doc_buffer)}
            response = requests.post(
                f"https://api.telegram.org/bot{self.token}/sendDocument",
                data={
                    "chat_id": chat_id,
                    "caption": text[:1024],  # Ограничение Telegram
                    "parse_mode": "Markdown",
                },
                files=files,
                timeout=10,
            )
            return response.status_code == 200
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка отправки документа в Telegram: {str(e)}")
            return False

    def _send_text_message(self, chat_id: str, text: str) -> bool:
        """Отправка текстового сообщения в Telegram"""
        try:
            response = requests.post(
                f"https://api.telegram.org/bot{self.token}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": text,
                    "parse_mode": "Markdown"
                },
                timeout=5,
            )
            return response.status_code == 200
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка отправки сообщения в Telegram: {str(e)}")
            return False


# Функции для обратной совместимости (можно постепенно переходить на ООП)
def generate_defect_statement(note):
    """Генерация дефектной ведомости (старая версия)"""
    return DefectStatementGenerator(note).generate()


def save_defect_statement(note):
    """Сохранение дефектной ведомости (старая версия)"""
    return DocumentService.save_defect_statement(note)


def send_to_telegram(note, chat_id=None):
    """Отправка в Telegram (старая версия)"""
    return TelegramNotificationService().send_notification(note, chat_id)
