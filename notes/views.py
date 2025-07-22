import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, DeleteView, TemplateView
from django.views.generic.edit import CreateView, UpdateView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from .models import Note
from .forms import NoteForm
from django.http import HttpResponse, FileResponse
import os
from django.conf import settings


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
        Представление для создания новой заметки.

        Attributes:
            model (Model): Модель Note для работы с записями
            form_class (Form): Класс формы для создания заметки
            template_name (str): Путь к шаблону отображения
            success_url (str): URL для перенаправления после успешного создания

        Methods:
            form_valid: Обработка валидной формы
            form_invalid: Обработка невалидной формы
    """
    model = Note
    form_class = NoteForm
    template_name = "notes/note_form.html"
    success_url = reverse_lazy("notes:list")

    def form_valid(self, form):
        """
            Обрабатывает валидную форму, устанавливает пользователя и логирует создание.

            Args:
                form (NoteForm): Валидная форма заметки

            Returns:
                HttpResponse: Редирект на success_url
        """
        form.instance.user = self.request.user
        response = super().form_valid(form)
        logger.info(f"Пользователь {self.request.user} создал новую заметку ID={self.object.pk}")
        messages.success(self.request, "Запись успешно создана!")
        return response

    def form_invalid(self, form):
        """Обработка ошибок при создании заметки"""

        logger.warning(
            f"Пользователь {self.request.user} не смог создать заметку. "
            f"Ошибки: {form.errors.as_json()}"
        )
        return super().form_invalid(form)

class NoteUpdateView(LoginRequiredMixin, UpdateView):
    """
        Представление для редактирования существующей заметки.

        Attributes:
            model (Model): Модель Note для работы с записями
            form_class (Form): Класс формы для редактирования заметки
            template_name (str): Путь к шаблону отображения
            context_object_name (str): Имя переменной контекста

        Methods:
            get_success_url: Возвращает URL для перенаправления после успешного обновления
            form_valid: Обработка валидной формы
            form_invalid: Обработка невалидной формы
    """
    model = Note
    form_class = NoteForm
    template_name = "notes/note_form.html"
    context_object_name = "note"

    def get_success_url(self):
        """Возвращает URL для перенаправления на страницу редактируемой заметки."""
        return reverse_lazy("notes:detail", kwargs={"pk": self.object.pk})

    def get_queryset(self):
        """Возвращает queryset заметок текущего пользователя с проверкой доступа."""
        return Note.objects.filter(user=self.request.user)

    def form_valid(self, form):
        """
            Обрабатывает валидную форму, логирует успешное обновление.

            Args:
                 form (NoteForm): Валидная форма заметки

            Returns:
                HttpResponse: Редирект на success_url
        """
        response = super().form_valid(form)
        logger.info(f"Пользователь {self.request.user} обновил заметку ID={self.object.pk}")
        messages.success(self.request, "Запись успешно обновлена!")
        return response

    def form_invalid(self, form):
        """
        Обрабатывает невалидную форму, логирует ошибки.

        Args:
            form (NoteForm): Невалидная форма заметки

        Returns:
            HttpResponse: Ответ с формой и ошибками
        """
        logger.warning(
            f"Пользователь {self.request.user} не смог обновить заметку ID={self.object.pk}. "
            f"Ошибки: {form.errors.as_json()}"
        )
        return super().form_invalid(form)


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


def download_document(request, pk):
    """
    Генерирует и скачивает документ в формате Word или Excel в зависимости от типа записи.

    Параметры:
        request (HttpRequest): Объект запроса Django
        pk (int): Первичный ключ (ID) записи Note

    Возвращает:
        FileResponse: Ответ с файлом для скачивания
        HttpResponseRedirect: Перенаправление с сообщением об ошибке, если что-то пошло не так

    Логика работы:
        1. Получает запись Note по ID, проверяя что она принадлежит текущему пользователю
        2. Определяет тип записи и соответствующий формат документа
        3. Генерирует документ через метод модели save_document_to_file()
        4. Проверяет существование сгенерированного файла
        5. Возвращает файл с правильными HTTP-заголовками для скачивания
        6. В случае ошибки перенаправляет на страницу записи с сообщением

    Исключения:
        Http404: Если заметка не найдена или нет прав доступа
    """

    logger.info(f"Пользователь {request.user} запросил скачивание документа для заметки ID={pk}")

    # Получаем запись или возвращаем 404
    note = get_object_or_404(Note, pk=pk, user=request.user)
    logger.debug(f"Найдена заметка: {note.title} (тип: {note.note_type})")

    # Определяем тип документа для генерации
    if note.note_type == "defect_statement":
        logger.debug("Генерация Word-документа для дефектной ведомости")
        document = note.save_document_to_file(format="word")   # Генерация Word-документа
    elif note.note_type == "hidden_act":
        logger.debug("Генерация Excel-документа для акта скрытых работ")
        document = note.save_document_to_file(format='excel')  # Генерация Excel-документа
    else:
        logger.warning(
            f"Для типа заметки '{note.note_type}' генерация документов не предусмотрена. "
            f"Заметка ID={pk}"
        )
        messages.warning(request, "Для этого типа записи документ не генерируется")
        return redirect("notes/detail", pk=pk)

    # Если документ успешно сгенерирован
    if document:
        file_path = os.path.join(settings.MEDIA_ROOT, document)
        logger.debug(f"Документ сгенерирован по пути: {file_path}")

        # Проверяем существование файла
        if os.path.exists(file_path):
            try:
            # Настройка ответа для Word
                if document.endswith(".docx"):
                    logger.info(f"Отправка Word-документа: {os.path.basename(file_path)}")
                    response = FileResponse(
                        open(file_path, "rb"),
                        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )
                    response['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'
                    return response

                # Настройка ответа для Excel
                elif document.endswith('.xlsx'):
                    logger.info(f"Отправка Excel-документа: {os.path.basename(file_path)}")
                    response = FileResponse(
                        open(file_path, 'rb'),
                        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                    )
                    response['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'
                    return response
            except Exception as e:
                logger.error(
                    f"Ошибка при отправке файла: {str(e)}\n"
                    f"Заметка ID={pk}, путь: {file_path}",
                    exc_info=True
                )
                messages.error(request, "Ошибка при отправке документа")
                return redirect('notes:detail', pk=pk)

    logger.error(
        f"Не удалось сгенерировать документ для заметки ID={pk}\n"
        f"Тип: {note.note_type}, документ: {document}"
    )
    # Если что-то пошло не так
    messages.error(request, "Не удалось сгенерировать документ")
    return redirect('notes:detail', pk=pk)
