from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.auth import get_user_model
from openpyxl import Workbook
from docx import Document
import os
from django.conf import settings

User = get_user_model()


# Create your models here.
class Note(models.Model):
    """Универсальная модель для всех записей"""
    NOTE_TYPE_CHOICES = [
        ("personal", "Личная запись"),
        ("work", "Рабочая запись"),
        ("defect_statement", "Дефектная ведомость"),
        ("hidden_act", "Акт скрытых работ"),
    ]

    # Общие поля
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    title = models.CharField(max_length=200, verbose_name="Заголовок")
    content = models.TextField(verbose_name="Содержание")
    image = models.ImageField(upload_to="notes/images", blank=True, null=True, verbose_name="Изображение")
    note_type = models.CharField(max_length=20, verbose_name="Тип записи", choices=NOTE_TYPE_CHOICES)

    # Поля для личных записей
    mood = models.CharField(max_length=100, verbose_name="Настроение", blank=True)
    is_private = models.BooleanField(verbose_name="Приватная", default=True)

    # Поля для рабочих документов
    object_name = models.CharField(max_length=250, verbose_name="Название объекта", blank=True)
    contractor = models.CharField(max_length=200, verbose_name="Подрядчик", blank=True)
    customer = models.CharField(max_length=200, verbose_name="Заказчик", blank=True)
    document = models.FileField(verbose_name="Документ", upload_to="work_docs/", blank=True)
    address = models.CharField(verbose_name='Адрес объекта', max_length=300, blank=True)

    # Специфичные поля для актов
    act_number = models.CharField(verbose_name="Номер акта", max_length=50, blank=True)
    inspection_date = models.DateField(verbose_name="Дата проверки", null=True, blank=True)

    # Специфичные поля для дефектных ведомостей
    statement_number = models.CharField(verbose_name="Номер ведомости", max_length=50, blank=True)
    approval_date = models.DateField(verbose_name="Дата утверждения", null=True, blank=True)
    approved_by = models.CharField(verbose_name='Утвердил', max_length=200, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Запись"
        verbose_name_plural = "Записи"

    def __str__(self):
        return f"{self.get_note_type_display()}: {self.title}"

    def generate_document(self):
        """Генерация документа в зависимости от типа записи"""
        if self.note_type == "hidden_act":
            return self._generate_act()
        elif self.note_type == "defect_statement":
            return self._generate_defect_statement()
        return None

    def _generate_act(self):
        """Генерация акта скрытых работ (Excel)"""
        wb = Workbook()
        ws = wb.active
        ws.title = "Акт скрытых работ"

        data = [
            ["Объект", self.object_name],
            ["Номер акта", self.act_number],
            ["Дата проверки", self.inspection_date.strftime("%d.%m.%Y") if self.inspection_date else ""],
            ["Заказчик", self.customer],
            ["Подрядчик", self.contractor],
            ["Содержание", self.content]
        ]

        for row in data:
            ws.append(row)

        return wb

    def _generate_defect_statement(self):
        """Генерация дефектной ведомости (Word)"""
        doc = Document()

        # Заголовок документа
        doc.add_heading(f"Дефектная ведомость № {self.statement_number}", level=1)
        doc.add_paragraph(f" на текущий ремонт помещения (здания)")

        # Информация об объекте
        doc.add_paragraph(f"Наименование объекта: {self.object_name}")
        doc.add_paragraph(f" Адрес объекта: {self.address}")

        # Таблица с дефектами
        table = doc.add_table(rows=1, cols=5)
        hdr_cells = table.rows[0].cells
        hdr_cells[0].text = "№ п/п"
        hdr_cells[1].text = "Обнаруженные дефекты и повреждения"
        hdr_cells[2].text = "Необходимые работы для устранения"
        hdr_cells[3].text = "Объем выявленных дефектов"
        hdr_cells[4].text = "Сроки устранения"

        # Заполнение таблицы данными
        if self.content:
            defects = self._parse_defects()
            for defect in defects:
                row_cells = table.add_row().cells
                row_cells[0].text = str(defect['number'])
                row_cells[1].text = defect['description']
                row_cells[2].text = defect['required_works']
                row_cells[3].text = defect['volume']
                row_cells[4].text = defect['deadline']

        # Подписи
        doc.add_paragraph("\nУтверждаю:")
        doc.add_paragraph(f"{self.approved_by}")
        doc.add_paragraph(f"Дата: {self.approval_date.strftime('%d.%m.%Y') if self.approval_date else ''}")

        return doc

    def _parse_defects(self):
        """Парсинг строк с дефектами из content"""
        defects = []

        for i, line in enumerate(self.content.split("\n")):
            if not line.strip():
                continue

            parts = [p.strip() for p in line.split("|")]

            defect = {
                "number": i + 1,
                "description": parts[0] if len(parts) > 0 else "",
                "required_works": parts[1] if len(parts) > 1 else "",
                "volume": parts[2] if len(parts) > 2 else "",
                "deadline": parts[3] if len(parts) > 3 else ""
            }
            defects.append(defect)

        return defects

    def save_document_to_file(self, format='word'):
        """Сохраняет документ в файл и возвращает путь к нему"""
        if self.note_type == "defect_statement" and format == 'word':
            doc = self._generate_defect_statement()
            filename = f"defect_statement_{self.id}.docx"
            filepath = os.path.join(settings.MEDIA_ROOT, "generated_docs", filename)
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            doc.save(filepath)
            return os.path.join("generated_docs", filename)

        elif self.note_type == "hidden_act" and format == 'excel':
            wb = self._generate_act()
            filename = f"hidden_act_{self.act_number}{self.id}.xlsx"
            filepath = os.path.join(settings.MEDIA_ROOT, "generated_docs", filename)
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            wb.save(filepath)
            return os.path.join("generated_docs", filename)

        return None

    def clean(self):
        """Валидация данных перед сохранением"""
        if self.note_type == "defect_statement":
            if not self.statement_number:
                raise ValidationError({"statement_number": "Для дефектной ведомости требуется номер"})
            if not self.object_name:
                raise ValidationError({"object_name": "Укажите наименование объекта"})

        if self.note_type == "hidden_act":  # Вынесено из блока defect_statement
            if not self.act_number:
                raise ValidationError({"act_number": "Для акта требуется номер"})
            if not self.inspection_date:
                raise ValidationError({"inspection_date": "Укажите дату проверки"})
