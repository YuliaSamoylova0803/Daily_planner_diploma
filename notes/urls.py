from django.urls import path
from notes.apps import NotesConfig
from .views import NoteListView, NoteCreateView, NoteUpdateView, NoteDetailView, NoteDeleteView, BaseView, \
    AddImagesView, download_document

app_name = NotesConfig.name  # или можно просто указать app_name = 'notes'

urlpatterns = [
    path("", BaseView.as_view(), name="base"),
    path("create/", NoteCreateView.as_view(), name="create"),
    path("<int:pk>/delete/", NoteDeleteView.as_view(), name="delete"),
    path("<int:pk>/update/", NoteUpdateView.as_view(), name="update"),
    path("<int:pk>/", NoteDetailView.as_view(), name="detail"),
    path("list/", NoteListView.as_view(), name="list"),
    path('<int:pk>/add-images/', AddImagesView.as_view(), name='add_images'),
    path('<int:pk>/download/', download_document, name='download_document'),

# Специальные URL для создания конкретных типов записей
    path('personal/create/', NoteCreateView.as_view(), name='create_personal'),
    path('work/create/', NoteCreateView.as_view(), name='create_work'),
    path('defect/create/', NoteCreateView.as_view(), name='create_defect'),
    path('statement/create/', NoteCreateView.as_view(), name='create_statement'),
]
