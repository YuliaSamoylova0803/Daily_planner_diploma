import os
import logging
from io import BytesIO
from django.conf import settings
from docx import Document
from docx.shared import Cm
import requests
from openpyxl import Workbook
from urllib.parse import quote
from django.utils import timezone

logger = logging.getLogger(__name__)



def generate_defect_statement(note):
    """
    Генерация дефектной ведомости в формате Word

    Args:
        note (Note): Объект модели Note с типом 'defect_statement'

    Returns:
        BytesIO: Байтовый поток с содержимым документа

    Raises:
        ValueError: Если передан объект неправильного типа
        IOError: При ошибках работы с изображениями
    """
    if note.note_type != 'defect_statement':
        raise ValueError("Эта функция предназначена только для дефектных ведомостей")

    doc = Document()

    try:
        # Заголовок документа
        doc.add_heading(f'Дефектная ведомость №{note.statement_number}', level=1)
        doc.add_paragraph(f'на текущий ремонт помещения (здания)')

        # Основная информация
        doc.add_paragraph(f'Наименование объекта: {note.object_name}')
        doc.add_paragraph(f'Адрес объекта: {note.address}')
        doc.add_paragraph(f'Дата составления: {timezone.now().strftime("%d.%m.%Y")}')

        # Таблица с дефектами
        table = _create_defects_table(doc, note)

        # Подписи
        _add_signatures_section(doc, note)

        # Сохраняем в BytesIO
        buffer = BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        return buffer

    except Exception as e:
        logger.error(f"Ошибка генерации документа: {str(e)}", exc_info=True)
        raise


def _create_defects_table(doc, note):
    """Создает и заполняет таблицу дефектов"""
    table = doc.add_table(rows=1, cols=6)
    table.style = 'Table Grid'

    # Настройка ширины колонок
    widths = (Cm(1.5), Cm(3.5), Cm(5), Cm(4), Cm(2), Cm(2.5))
    for i, width in enumerate(widths):
        table.columns[i].width = width

    # Заголовки таблицы
    headers = ["№ п/п", "Фото дефекта", "Обнаруженные дефекты",
               "Необходимые работы", "Объем", "Сроки"]

    for i, header in enumerate(headers):
        cell = table.rows[0].cells[i]
        cell.text = header
        cell.paragraphs[0].runs[0].font.bold = True

    # Заполнение данными
    for i, defect in enumerate(note.defects.all().order_by('created_at'), start=1):
        row_cells = table.add_row().cells
        row_cells[0].text = str(i)
        row_cells[2].text = defect.content
        row_cells[3].text = defect.title

        # Добавление изображения
        _add_defect_image(row_cells[1], defect)

    return table


def _add_defect_image(cell, defect):
    """Добавляет изображение дефекта в ячейку таблицы"""
    if defect.images.exists():
        try:
            image = defect.images.first()
            paragraph = cell.paragraphs[0]
            run = paragraph.add_run()
            run.add_picture(image.image.path, width=Cm(3), height=Cm(2))
        except Exception as e:
            logger.warning(f"Не удалось добавить изображение для дефекта {defect.id}: {str(e)}")
            cell.text = "Фото (ошибка загрузки)"


def _add_signatures_section(doc, note):
    """Добавляет раздел с подписями"""
    doc.add_paragraph("\nСоставил: _________________________")
    if note.approved_by:
        doc.add_paragraph(f"\nУтверждаю: {note.approved_by}")
    if note.approval_date:
        doc.add_paragraph(f"Дата: {note.approval_date.strftime('%d.%m.%Y')}")


def save_defect_statement(note):
    """
    Сохраняет дефектную ведомость в файл

    Args:
        note (Note): Объект модели Note

    Returns:
        str: Относительный путь к файлу от MEDIA_ROOT

    Raises:
        IOError: При ошибках записи файла
    """
    try:
        doc_buffer = generate_defect_statement(note)
        filename = f"defect_statement_{note.id}_{timezone.now().strftime('%Y%m%d_%H%M')}.docx"
        filename = quote(filename)  # Экранируем специальные символы
        filepath = os.path.join(settings.MEDIA_ROOT, "generated_docs", filename)

        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        with open(filepath, 'wb') as f:
            f.write(doc_buffer.getvalue())

        return os.path.join("generated_docs", filename)
    except Exception as e:
        logger.error(f"Ошибка сохранения документа: {str(e)}", exc_info=True)
        raise


def send_to_telegram(note, chat_id=None):
    """
    Отправляет уведомление в Telegram

    Args:
        note (Note): Объект модели Note для отправки
        chat_id (str, optional): ID чата для отправки

    Returns:
        bool: True если отправка успешна, False в случае ошибки
    """
    try:
        TELEGRAM_TOKEN = getattr(settings, 'TELEGRAM_TOKEN', '')
        TELEGRAM_CHAT_ID = chat_id or getattr(settings, 'TELEGRAM_CHAT_ID', '')

        if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
            logger.warning("Не настроены Telegram credentials")
            return False

        base_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
        text = _prepare_telegram_message(note)

        if note.note_type == 'defect_statement':
            return _send_telegram_document(base_url, TELEGRAM_CHAT_ID, note, text)
        return _send_telegram_message(base_url, TELEGRAM_CHAT_ID, text)

    except Exception as e:
        logger.error(f"Ошибка отправки в Telegram: {str(e)}", exc_info=True)
        return False


def _prepare_telegram_message(note):
    """Формирует текст сообщения для Telegram"""
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


def _send_telegram_document(base_url, chat_id, note, text):
    """Отправляет документ в Telegram"""
    try:
        doc_buffer = generate_defect_statement(note)
        files = {'document': (f'defect_{note.id}.docx', doc_buffer)}
        response = requests.post(
            f"{base_url}/sendDocument",
            data={
                'chat_id': chat_id,
                'caption': text[:1024],  # Ограничение Telegram
                'parse_mode': 'Markdown'
            },
            files=files,
            timeout=10
        )
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка отправки документа в Telegram: {str(e)}")
        return False


def _send_telegram_message(base_url, chat_id, text):
    """Отправляет текстовое сообщение в Telegram"""
    try:
        response = requests.post(
            f"{base_url}/sendMessage",
            json={
                'chat_id': chat_id,
                'text': text,
                'parse_mode': 'Markdown'
            },
            timeout=5
        )
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка отправки сообщения в Telegram: {str(e)}")
        return False
