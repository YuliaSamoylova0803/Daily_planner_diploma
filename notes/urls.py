from django.urls import path
from notes.apps import NotesConfig
from .views import (
    BaseView,
    DefectImageCreateView,
    DefectStatementCreateView,
    DefectStatementDetailView,
    DefectStatementListView,
    NoteCreateView,
    NoteDeleteView,
    NoteDetailView,
    NoteListView,
    NoteUpdateView,
    download_statement,
    send_to_telegram_view,
)
from .api import send_to_telegram_api  # Импортируем новую API view

app_name = NotesConfig.name

urlpatterns = [
    path("", BaseView.as_view(), name="base"),
    path("create/", NoteCreateView.as_view(), name="create"),
    path("<int:pk>/delete/", NoteDeleteView.as_view(), name="delete"),
    path("<int:pk>/update/", NoteUpdateView.as_view(), name="update"),
    path("<int:pk>/", NoteDetailView.as_view(), name="detail"),
    path("list/", NoteListView.as_view(), name="list"),
    path(
        "<int:note_id>/add-defect-image/",
        DefectImageCreateView.as_view(),
        name="add_defect_image",
    ),
    path("<int:pk>/download/", download_statement, name="download_document"),
    path("<int:pk>/send_telegram/", send_to_telegram_view, name="send_to_telegram"),
    # Новый API endpoint для AJAX-запросов
    path(
        "api/send-to-telegram/<int:pk>/",
        send_to_telegram_api,
        name="send_to_telegram_api",
    ),
    # Специальные URL для создания конкретных типов записей
    path(
        "personal/create/",
        NoteCreateView.as_view(),
        {"note_type": "personal"},
        name="create_personal",
    ),
    path(
        "work/create/",
        NoteCreateView.as_view(),
        {"note_type": "work"},
        name="create_work",
    ),
    path(
        "defect/create/",
        NoteCreateView.as_view(),
        {"note_type": "defect"},
        name="create_defect",
    ),
    path(
        "statement/create/",
        NoteCreateView.as_view(),
        {"note_type": "statement"},
        name="create_statement",
    ),
    # URL для дефектных ведомостей
    path(
        "defect-statements/",
        DefectStatementListView.as_view(),
        name="defect_statement_list",
    ),
    path(
        "defect-statements/create/",
        DefectStatementCreateView.as_view(),
        name="defect_statement_create",
    ),
    path(
        "defect-statements/<int:pk>/",
        DefectStatementDetailView.as_view(),
        name="defect_statement_detail",
    ),
    path(
        "defect-statements/<int:pk>/download/",
        download_statement,
        name="defect_statement_download",
    ),
]
