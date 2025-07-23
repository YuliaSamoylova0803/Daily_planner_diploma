from django.urls import path
from notes.apps import NotesConfig
from .views import NoteListView, NoteCreateView, NoteUpdateView, NoteDetailView, NoteDeleteView, download_document, \
    BaseView, generate_document

app_name = NotesConfig.name  # или можно просто указать app_name = 'notes'

urlpatterns = [
    path("", BaseView.as_view(), name="base"),
    path("create/", NoteCreateView.as_view(), name="create"),
    path("<int:pk>/delete/", NoteDeleteView.as_view(), name="delete"),
    path("<int:pk>/update/", NoteUpdateView.as_view(), name="update"),
    path("<int:pk>/download/", download_document, name="download"),
    path("<int:pk>/", NoteDetailView.as_view(), name="detail"),
    path("list/", NoteListView.as_view(), name="list"),
    path('<int:pk>/generate/', generate_document, name='generate_document'),
]
