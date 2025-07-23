from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, DeleteView, TemplateView
from django.views.generic.edit import CreateView, UpdateView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from .models import Note
from .forms import get_note_form_class, NoteImageForm
from django.http import HttpResponse, FileResponse
import os
from django.conf import settings
import logging
from .services import save_defect_statement



logger = logging.getLogger(__name__)


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

        logger.debug(f"Пользователь {self.request.user} запросил просмотр заметки ID={self.kwargs['pk']}")
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
        """Возвращает соответствующую форму на основе типа записи"""
        note_type = self.request.GET.get('note_type', 'personal')
        return get_note_form_class(note_type)

    def form_valid(self, form):
        """Обработка валидной формы - установка пользователя и типа записи"""
        form.instance.user = self.request.user
        form.instance.note_type = self.request.GET.get('note_type', 'personal')
        response = super().form_valid(form)
        logger.info(
            f"Пользователь {self.request.user} создал {form.instance.get_note_type_display()} ID={self.object.pk}")
        messages.success(self.request, "Запись успешно создана!")
        return response

    def get_success_url(self):
        """Перенаправление после успешного создания"""
        if self.object.note_type in ['defect', 'defect_statement']:
            return reverse_lazy('notes:add_images', kwargs={'pk': self.object.pk})
        return reverse_lazy('notes:list')


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
            f"Пользователь {self.request.user} обновил {form.instance.get_note_type_display()} ID={self.object.pk}")
        messages.success(self.request, "Запись успешно обновлена!")
        return response

    def get_success_url(self):
        """Перенаправление после успешного обновления"""
        return reverse_lazy('notes:detail', kwargs={'pk': self.object.pk})


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
        messages.success(request, 'Запись успешно удалена!')
        return response


class AddImagesView(LoginRequiredMixin, UpdateView):
    """
    Представление для добавления изображений к записи.

    Особенности:
    - Работает только с записями типа 'defect' и 'defect_statement'
    - Использует отдельную форму для загрузки изображений
    """
    model = Note
    template_name = "notes/add_images.html"
    fields = []

    def get_queryset(self):
        """Ограничивает доступ только к записям текущего пользователя"""
        return Note.objects.filter(
            user=self.request.user,
            note_type__in=['defect', 'defect_statement']
        )

    def get_context_data(self, **kwargs):
        """Добавляет в контекст форму для загрузки изображений"""
        context = super().get_context_data(**kwargs)
        context['image_form'] = NoteImageForm()
        context['images'] = self.object.images.all()
        return context

    def post(self, request, *args, **kwargs):
        """Обработка загрузки изображений"""
        self.object = self.get_object()
        image_form = NoteImageForm(request.POST, request.FILES)

        if image_form.is_valid():
            image = image_form.save(commit=False)
            image.note = self.object
            image.save()
            messages.success(request, "Изображение успешно добавлено!")
            return redirect('notes:add_images', pk=self.object.pk)

        messages.error(request, "Ошибка при загрузке изображения")
        return self.render_to_response(
            self.get_context_data(image_form=image_form))

    def get_success_url(self):
        return reverse_lazy('notes:add_images', kwargs={'pk': self.object.pk})


def download_document(request, pk):
    """
    Генерирует и скачивает документ в зависимости от типа записи.

    Улучшения:
    1. Поддержка только актуальных типов документов (без hidden_act)
    2. Использование services.py для генерации
    3. Улучшенное логирование и обработка ошибок
    4. Безопасная работа с путями файлов
    5. Человекочитаемые имена файлов при скачивании
    """
    relative_path = save_defect_statement(note)
    logger.info(f"User {request.user} requested document download for note ID={pk}")

    try:
        note = get_object_or_404(Note, pk=pk, user=request.user)

        if note.note_type != "defect_statement":
            logger.warning(f"Document generation not supported for type: {note.note_type}")
            messages.warning(request, "Документ доступен только для дефектных ведомостей")
            return redirect('notes:detail', pk=pk)

        # Генерация документа через сервисный слой
        from .services import save_defect_statement
        relative_path = save_defect_statement(note)
        absolute_path = os.path.join(settings.MEDIA_ROOT, relative_path)

        if not os.path.exists(absolute_path):
            raise FileNotFoundError(f"Generated document not found at {absolute_path}")

        # Формирование читаемого имени файла
        filename = f"Дефектная ведомость {note.statement_number or note.id}.docx"
        safe_filename = filename.replace(" ", "_")

        logger.info(f"Serving document: {absolute_path}")
        response = FileResponse(
            open(absolute_path, 'rb'),
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            as_attachment=True,
            filename=safe_filename
        )

        # Добавляем оригинальное имя файла в заголовки
        response['X-Filename'] = filename
        return response

    except Exception as e:
        logger.error(f"Document generation failed for note {pk}: {str(e)}", exc_info=True)
        messages.error(request, f"Ошибка при генерации документа: {str(e)}")
        return redirect('notes:detail', pk=pk)
