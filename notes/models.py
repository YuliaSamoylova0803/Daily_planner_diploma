from django.contrib.auth import get_user_model
from django.db import models

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
    note_type = models.CharField(
        max_length=20, verbose_name="Тип записи", choices=NOTE_TYPE_CHOICES
    )
    title = models.CharField(max_length=200, verbose_name="Заголовок")
    content = models.TextField(verbose_name="Содержание", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    image = models.ImageField(
        upload_to="notes/images", blank=True, null=True, verbose_name="Изображение"
    )

    # Поля для личных записей
    mood = models.CharField(max_length=100, verbose_name="Настроение", blank=True)
    is_private = models.BooleanField(verbose_name="Приватная", default=True)

    # Поля для рабочих записей и дефектов
    object_name = models.CharField(
        max_length=250, verbose_name="Название объекта", blank=True
    )
    address = models.CharField(verbose_name="Адрес объекта", max_length=300, blank=True)

    # Поля только для дефектной ведомости
    statement_number = models.CharField(
        verbose_name="Номер ведомости", max_length=50, blank=True
    )
    approval_date = models.DateField(
        verbose_name="Дата утверждения", null=True, blank=True
    )
    approved_by = models.CharField(verbose_name="Утвердил", max_length=200, blank=True)

    defects = models.ManyToManyField(
        "self", blank=True, limit_choices_to={"note_type": "defect"}
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Запись"
        verbose_name_plural = "Записи"

    def __str__(self):
        return f"{self.get_note_type_display()}: {self.title}"


class DefectImage(models.Model):
    """Модель для изображений дефектов с описанием"""

    note = models.ForeignKey(
        Note,
        on_delete=models.CASCADE,
        related_name="defect_images",
        limit_choices_to={"note_type": "defect"},  # Связь только с дефектами
    )
    image = models.ImageField(
        upload_to="defects/%Y/%m/%d/", verbose_name="Фото дефекта"
    )
    description = models.TextField(verbose_name="Описание дефекта", blank=True)
    required_work = models.TextField(verbose_name="Необходимые работы", blank=True)
    repair_deadline = models.DateField(
        verbose_name="Срок устранения", null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Изображение дефекта"
        verbose_name_plural = "Изображения дефектов"
        ordering = ["created_at"]

    def __str__(self):
        return f"Фото дефекта #{self.id}"


class DefectStatement(models.Model):
    """Дефектная ведомость"""

    title = models.CharField(max_length=200, verbose_name="Название ведомости")
    statement_number = models.CharField(max_length=50, verbose_name="Номер ведомости")

    created_at = models.DateTimeField(auto_now_add=True)
    approval_date = models.DateField(
        verbose_name="Дата утверждения", null=True, blank=True
    )
    approved_by = models.CharField(verbose_name="Утвердил", max_length=200, blank=True)
    defects = models.ManyToManyField(
        Note, through="DefectInStatement", limit_choices_to={"note_type": "defect"}
    )
    author = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"Дефектная ведомость №{self.statement_number}"


class DefectInStatement(models.Model):
    """Связь дефектов с ведомостью"""

    defect = models.ForeignKey(Note, on_delete=models.CASCADE)
    statement = models.ForeignKey(DefectStatement, on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]
