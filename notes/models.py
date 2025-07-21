from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.contrib.auth import get_user_model
from openpyxl import Workbook
from docx import Document
import os
from django.conf import settings
from docx.shared import Cm


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
        """Генерация дефектной ведомости (Word) с изображениями"""
        doc = Document()

        # Заголовок документа
        doc.add_heading(f"Дефектная ведомость № {self.statement_number}", level=1)
        doc.add_paragraph(f" на текущий ремонт помещения (здания)")

        # Информация об объекте
        doc.add_paragraph(f"Наименование объекта: {self.object_name}")
        doc.add_paragraph(f" Адрес объекта: {self.address}")


        # Таблица с дефектами
        table = doc.add_table(rows=1, cols=6)

        # Установка ширины колонок
        table.autofit = False
        table.columns[0].width = Cm(1.5)  # № п/п
        table.columns[1].width = Cm(3.5)  # Фото
        table.columns[2].width = Cm(5)  # Описание
        table.columns[3].width = Cm(4)  # Работы
        table.columns[4].width = Cm(2)  # Объем
        table.columns[5].width = Cm(2.5)  # Сроки

        # Установка стиля таблицы с границами
        table.style = 'Table Grid'

        # Заголовки таблицы
        hdr_cells = table.rows[0].cells
        hdr_cells[0].text = "№ п/п"
        hdr_cells[1].text = "Фото дефекта"
        hdr_cells[2].text = "Обнаруженные дефекты и повреждения"
        hdr_cells[3].text = "Необходимые работы для устранения"
        hdr_cells[4].text = "Объем выявленных дефектов"
        hdr_cells[5].text = "Сроки устранения"

        # Жирный шрифт для заголовков
        for cell in hdr_cells:
            for paragraph in cell.paragraphs:
                for run in paragraph.runs:
                    run.font.bold = True

        # Заполнение таблицы данными
        if self.content:
            defects = self._parse_defects()
            for defect in defects:
                row_cells = table.add_row().cells

                # № п/п
                row_cells[0].text = str(defect['number'])

                # Ячейка для фото (оставляем пустой, фото добавим ниже)
                row_cells[1].text = ""

                # Остальные данные
                row_cells[2].text = defect['description']
                row_cells[3].text = defect['required_works']
                row_cells[4].text = defect['volume']
                row_cells[5].text = defect['deadline']

                # Добавляем фото дефекта, если оно есть
                if defect.get("image_path") and os.path.exists(defect["image_path"]):
                    try:
                        # Уменьшаем размер ячейки для фото
                        row_cells[1].width = Cm(3)  # Ширина 3 см

                        # Добавляем фото с уменьшением размера
                        paragraph = row_cells[1].paragraphs[0]
                        run = paragraph.add_run()
                        run.add_picture(
                            defect["image_path"],
                            width=Cm(3),   # Ширина 3 см
                            height=Cm(2))   # Высота 2 см (сохранит пропорции)
                    except Exception as e:
                        print(f"Ошибка при добавлении изображения: {e}")
                        row_cells[1].text = "Фото не загружено"


        # Подписи
        doc.add_paragraph("\nУтверждаю:")
        doc.add_paragraph(f"{self.approved_by}")
        doc.add_paragraph(f"Дата: {self.approval_date.strftime('%d.%m.%Y') if self.approval_date else ''}")

        return doc

    def _parse_defects(self):
        """Парсинг строк с дефектами из content с учетом изображений"""
        defects = []

        for i, line in enumerate(self.content.split("\n")):
            if not line.strip():
                continue

            parts = [p.strip() for p in line.split("|")]

            # Получаем изображение для этого дефекта
            defect_images = self.defect_images.filter(defect_number=i+1)
            image_paths = [img.image.path for img in defect_images if img.image and os.path.exists(img.image.path)]

            defect = {
                "number": i + 1,
                "description": parts[0] if len(parts) > 0 else "",
                "required_works": parts[1] if len(parts) > 1 else "",
                "volume": parts[2] if len(parts) > 2 else "",
                "deadline": parts[3] if len(parts) > 3 else "",
                "image_path": image_paths[0] if image_paths else None
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


class DefectImage(models.Model):
    note = models.ForeignKey(Note, on_delete=models.CASCADE, related_name='defect_images')
    image = models.ImageField(verbose_name="Фото дефекта", upload_to="defect_images/")
    defect_number = models.IntegerField(verbose_name="Номер дефекта", validators=[MinValueValidator(1)])  # Номер дефекта из content
    description = models.CharField(max_length=200, blank=True, verbose_name="Описание")

    class Meta:
        verbose_name = "Изображение дефекта"
        verbose_name_plural = "Изображения дефектов"
        ordering = ["note", "defect_number"]
        indexes = [
            models.Index(fields=["note", "defect_number"]),
        ]

    def __str__(self):
        return f"Изображение дефекта {self.defect_number} для {self.note.title}"
