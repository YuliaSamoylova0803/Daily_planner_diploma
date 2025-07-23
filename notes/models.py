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
    ]

    # Общие поля
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    note_type = models.CharField(max_length=20, verbose_name="Тип записи", choices=NOTE_TYPE_CHOICES)
    title = models.CharField(max_length=200, verbose_name="Заголовок")
    content = models.TextField(verbose_name="Содержание", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    image = models.ImageField(upload_to="notes/images", blank=True, null=True, verbose_name="Изображение")


    # Поля для личных записей
    mood = models.CharField(max_length=100, verbose_name="Настроение", blank=True)
    is_private = models.BooleanField(verbose_name="Приватная", default=True)

    # Поля для рабочих записей и дефектов
    object_name = models.CharField(max_length=250, verbose_name="Название объекта", blank=True)
    address = models.CharField(verbose_name='Адрес объекта', max_length=300, blank=True)

    # Поля только для дефектной ведомости
    statement_number = models.CharField(verbose_name="Номер ведомости", max_length=50, blank=True)
    approval_date = models.DateField(verbose_name="Дата утверждения", null=True, blank=True)
    approved_by = models.CharField(verbose_name='Утвердил', max_length=200, blank=True)

    defects = models.ManyToManyField("self", blank=True, limit_choices_to={"note_type": "defect"})

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Запись"
        verbose_name_plural = "Записи"

    def __str__(self):
        return f"{self.get_note_type_display()}: {self.title}"


class NoteImage(models.Model):
    note = models.ForeignKey(Note, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(verbose_name="Фото", upload_to="note_images/")
    description = models.CharField(max_length=200, blank=True, verbose_name="Описание")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Изображение дефекта для {self.note.title}"
