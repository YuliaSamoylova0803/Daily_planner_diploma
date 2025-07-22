from django.urls import path
from notes.apps import NotesConfig
from .views import NoteListView, NoteCreateView, NoteUpdateView, NoteDetailView, NoteDeleteView, download_document

app_name = NotesConfig.name  # или можно просто указать app_name = 'notes'

urlpatterns = [
    path("create/", NoteCreateView.as_view(), name="create"),
    path("<int:pk>/delete/", NoteDeleteView.as_view(), name="delete"),
    path("<int:pk>/update/", NoteUpdateView.as_view(), name="update"),
    path("<int:pk>/download/", download_document, name="download"),
    path("<int:pk>/", NoteDetailView.as_view(), name="detail"),
    path("", NoteListView.as_view(), name="list"),
]
