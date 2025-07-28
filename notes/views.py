import logging
from io import BytesIO

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import FileResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import DeleteView, DetailView, ListView, TemplateView
from django.views.generic.edit import CreateView, UpdateView
from docx import Document

from .forms import (
    DefectImageForm,
    DefectNoteForm,
    DefectStatementForm,
    PersonalNoteForm,
    WorkNoteForm,
    get_note_form_class,
)
from .models import DefectImage, DefectStatement, Note
from .services import send_to_telegram as send_to_telegram_service

logger = logging.getLogger(__name__)

NOTE_TYPES = (
    ("personal", "Личная запись"),
    ("work", "Рабочая запись"),
    ("defect", "Дефект"),
    ("statement", "Ведомость"),
)


def base(request):
    return render(request, "notes/base.html")


class BaseView(TemplateView):
    template_name = "notes/base.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Общее количество записей
        total_notes = Note.objects.count()

        context.update(
            {
                "total_notes": total_notes,
            }
        )
        return context


class NoteListView(LoginRequiredMixin, ListView):
    """
    Представление для отображения списка всех заметок пользователя.

    Attributes:
        model (Model): Модель Note для работы с записями
        template_name (str): Путь к шаблону отображения
        context_object_name (str): Имя переменной контекста
        paginate_by (int): Количество элементов на странице

    Methods:
        get_queryset: Возвращает отфильтрованный и отсортированный queryset
    """

    model = Note
    login_url = reverse_lazy("users:login")
    redirect_field_name = "next"
    template_name = "notes/note_list.html"
    context_object_name = "notes"
    paginate_by = 10

    def get_queryset(self):
        """Возвращает queryset заметок текущего пользователя, отсортированный по дате создания."""

        logger.debug(f"Пользователь {self.request.user} запросил список своих заметок")
        return Note.objects.filter(user=self.request.user).order_by("-created_at")


class NoteDetailView(LoginRequiredMixin, DetailView):
    """
    Представление для детального просмотра конкретной заметки.

    Attributes:
        model (Model): Модель Note для работы с записями
        template_name (str): Путь к шаблону отображения
        context_object_name (str): Имя переменной контекста

    Methods:
        get_queryset: Возвращает queryset с проверкой принадлежности заметки пользователю
    """

    model = Note
    template_name = "notes/note_detail.html"
    context_object_name = "note"

    def get_queryset(self):
        """Возвращает queryset заметок текущего пользователя с проверкой доступа."""

        logger.debug(
            f"Пользователь {self.request.user} запросил просмотр заметки ID={self.kwargs['pk']}"
        )
        return Note.objects.filter(user=self.request.user)


class NoteCreateView(LoginRequiredMixin, CreateView):
    """
    Представление для создания новой заметки с автоматическим выбором формы.

    Особенности:
    - Определяет тип записи из GET-параметра (note_type)
    - Использует фабрику форм get_note_form_class для выбора нужной формы
    - Автоматически устанавливает пользователя и тип записи
    """

    model = Note
    template_name = "notes/note_form.html"

    def get_form_class(self):
        note_type = self.kwargs.get("note_type") or self.request.GET.get("note_type")

        if note_type == "personal":
            return PersonalNoteForm
        elif note_type == "work":
            return WorkNoteForm
        elif note_type == "defect":
            return DefectNoteForm
        elif note_type == "statement":
            return DefectStatementForm
        else:
            # Форма по умолчанию или обработка ошибки
            from django import forms

            class DefaultNoteForm(forms.ModelForm):
                class Meta:
                    model = Note  # Укажите вашу модель
                    fields = ["title", "content"]

            return DefaultNoteForm

    def get_note_type(self):
        return self.kwargs.get("note_type") or self.request.GET.get("note_type")

    def get_note_type_display(self):
        note_type = self.get_note_type()
        return dict(NOTE_TYPES).get(note_type, "новой")

    def form_valid(self, form):
        """Обработка валидной формы - установка пользователя и типа записи"""
        form.instance.user = self.request.user
        form.instance.note_type = self.request.GET.get("note_type", "personal")
        response = super().form_valid(form)
        logger.info(
            f"Пользователь {self.request.user} создал {form.instance.get_note_type_display()} ID={self.object.pk}"
        )
        messages.success(self.request, "Запись успешно создана!")
        return response

    def get_success_url(self):
        """Перенаправление после успешного создания"""
        if self.object.note_type == "defect":
            return reverse_lazy(
                "notes:add_defect_image", kwargs={"note_id": self.object.pk}
            )
        elif self.object.note_type == "defect_statement":
            return reverse_lazy(
                "notes:defect_statement_detail", kwargs={"pk": self.object.pk}
            )
        return reverse_lazy("notes:list")


class NoteUpdateView(LoginRequiredMixin, UpdateView):
    """
    Представление для редактирования существующей заметки.

    Особенности:
    - Автоматически выбирает форму на основе типа записи
    - Проверяет, что запись принадлежит текущему пользователю
    - Сохраняет логи изменений
    """

    model = Note
    template_name = "notes/note_form.html"

    def get_form_class(self):
        """Возвращает соответствующую форму на основе типа записи"""
        return get_note_form_class(self.object.note_type)

    def get_queryset(self):
        """Ограничивает доступ только к записям текущего пользователя"""
        return Note.objects.filter(user=self.request.user)

    def form_valid(self, form):
        """Обработка успешного обновления записи"""
        response = super().form_valid(form)
        logger.info(
            f"Пользователь {self.request.user} обновил {form.instance.get_note_type_display()} ID={self.object.pk}"
        )
        messages.success(self.request, "Запись успешно обновлена!")
        return response

    def get_success_url(self):
        """Перенаправление после успешного обновления"""
        return reverse_lazy("notes:detail", kwargs={"pk": self.object.pk})


class NoteDeleteView(LoginRequiredMixin, DeleteView):
    """
    Представление для удаления заметки.

    Attributes:
        model (Model): Модель Note для работы с записями
        template_name (str): Путь к шаблону подтверждения удаления
        success_url (str): URL для перенаправления после удаления
        context_object_name (str): Имя переменной контекста

    Methods:
        get_queryset: Возвращает queryset с проверкой принадлежности заметки
        delete: Выполняет удаление и логирует операцию
    """

    model = Note
    template_name = "notes/note_confirm_delete.html"
    success_url = reverse_lazy("notes:list")
    context_object_name = "note"

    def get_queryset(self):
        """Возвращает queryset заметок текущего пользователя с проверкой доступа."""
        return Note.objects.filter(user=self.request.user)

    def delete(self, request, *args, **kwargs):
        """
        Выполняет удаление заметки, логирует операцию и показывает сообщение.

        Args:
            request (HttpRequest): Объект запроса
            *args: Аргументы
            **kwargs: Именованные аргументы

        Returns:
            HttpResponse: Редирект на success_url
        """
        note_pk = self.get_object().pk
        response = super().delete(request, *args, **kwargs)
        logger.info(f"Пользователь {request.user} удалил заметку ID={note_pk}")
        messages.success(request, "Запись успешно удалена!")
        return response


class DefectImageCreateView(CreateView):
    model = DefectImage
    form_class = DefectImageForm
    template_name = "notes/add_defect_image.html"

    def get_success_url(self):
        return reverse_lazy("notes:detail", kwargs={"pk": self.kwargs["note_id"]})

    def form_valid(self, form):
        form.instance.note_id = self.kwargs["note_id"]
        return super().form_valid(form)


# class AddImagesView(LoginRequiredMixin, UpdateView):
#     """
#     Представление для добавления изображений к записи.
#
#     Особенности:
#     - Работает только с записями типа 'defect' и 'defect_statement'
#     - Использует отдельную форму для загрузки изображений
#     """
#     model = Note
#     template_name = "notes/add_images.html"
#     fields = []
#
#     def get_queryset(self):
#         """Ограничивает доступ только к записям текущего пользователя"""
#         return Note.objects.filter(
#             user=self.request.user,
#             note_type__in=['defect', 'defect_statement']
#         )
#
#     def get_context_data(self, **kwargs):
#         """Добавляет в контекст форму для загрузки изображений"""
#         context = super().get_context_data(**kwargs)
#         context['images'] = self.object.images.all()
#         return context
#
#     def post(self, request, *args, **kwargs):
#         """Обработка загрузки изображений"""
#         self.object = self.get_object()
#         image_form = NoteImageForm(request.POST, request.FILES)
#
#         if image_form.is_valid():
#             image = image_form.save(commit=False)
#             image.note = self.object
#             image.save()
#             messages.success(request, "Изображение успешно добавлено!")
#             return redirect('notes:add_images', pk=self.object.pk)
#
#         messages.error(request, "Ошибка при загрузке изображения")
#         return self.render_to_response(
#             self.get_context_data(image_form=image_form))
#
#     def get_success_url(self):
#         return reverse_lazy('notes:add_images', kwargs={'pk': self.object.pk})


class DefectStatementCreateView(LoginRequiredMixin, CreateView):
    model = DefectStatement
    form_class = DefectStatementForm
    template_name = "notes/defect_statement_form.html"

    def form_valid(self, form):
        form.instance.author = self.request.user
        response = super().form_valid(form)
        # Сохраняем порядок дефектов
        for order, defect in enumerate(form.cleaned_data["defects"], start=1):
            self.object.defectinstatement_set.create(defect=defect, order=order)
        return response

    def get_success_url(self):
        return reverse_lazy(
            "notes:defect_statement_detail", kwargs={"pk": self.object.pk}
        )


class DefectStatementListView(LoginRequiredMixin, ListView):
    model = DefectStatement
    template_name = "notes/defect_statement_list.html"
    context_object_name = "statements"
    paginate_by = 10


class DefectStatementDetailView(LoginRequiredMixin, DetailView):
    model = DefectStatement
    template_name = "notes/defect_statement_detail.html"
    context_object_name = "statement"


def download_statement(request, pk):
    statement = DefectStatement.objects.get(pk=pk)
    doc = Document()

    # Заголовок
    doc.add_heading(f"Дефектная ведомость №{statement.statement_number}", level=1)
    doc.add_paragraph(statement.title)

    # Таблица дефектов
    table = doc.add_table(rows=1, cols=5)
    table.style = "Table Grid"

    # Заголовки таблицы
    hdr = table.rows[0].cells
    hdr[0].text = "№"
    hdr[1].text = "Дефект"
    hdr[2].text = "Описание"
    hdr[3].text = "Фото"
    hdr[4].text = "Рекомендации"

    # Заполнение таблицы
    for idx, item in enumerate(statement.defectinstatement_set.all(), start=1):
        row = table.add_row().cells
        defect = item.defect
        row[0].text = str(idx)
        row[1].text = defect.title
        row[2].text = defect.content[:100]
        row[3].text = "Есть" if defect.defect_images.exists() else "Нет"

        # Берем первую рекомендацию из изображений дефекта
        first_img = defect.defect_images.first()
        row[4].text = first_img.description if first_img else ""

    # Генерация файла
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)

    filename = f"defect_statement_{statement.statement_number}.docx"
    return FileResponse(buffer, as_attachment=True, filename=filename)


def send_to_telegram_view(request, pk):
    """
    View для обработки отправки в Telegram
    """
    note = get_object_or_404(Note, pk=pk, user=request.user)

    if note.note_type not in ["defect_statement", "hidden_act"]:
        messages.error(request, "Этот тип записи нельзя отправить в Telegram")
        return redirect("notes:detail", pk=pk)

    # Вызываем сервисный метод с новым именем
    success = send_to_telegram_service(note)

    if success:
        messages.success(request, "Запись успешно отправлена в Telegram")
    else:
        messages.error(request, "Ошибка при отправке в Telegram")

    return redirect("notes:detail", pk=pk)
