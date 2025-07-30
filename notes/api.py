from django.contrib.auth.decorators import login_required
from django.http import FileResponse, JsonResponse
from drf_yasg import openapi

from rest_framework.generics import get_object_or_404

from .models import Note
from rest_framework.decorators import api_view
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from .services import (
    DefectStatementGenerator,
    TelegramNotificationService,
)
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from .models import DefectStatement
from .services import send_to_telegram


@swagger_auto_schema(
    method="post",
    operation_summary="Генерация ведомости",
    operation_description="Создает DOCX файл дефектной ведомости",
    responses={
        200: openapi.Response(
            "File attachment", schema=openapi.Schema(type=openapi.TYPE_FILE)
        ),
        400: openapi.Response(
            "Bad Request",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={"error": openapi.Schema(type=openapi.TYPE_STRING)},
            ),
        ),
    },
)
@api_view(["POST"])
def generate_statement(request, pk):
    note = get_object_or_404(Note, pk=pk)
    try:
        generator = DefectStatementGenerator(note)
        doc_buffer = generator.generate()
        return FileResponse(doc_buffer, filename=f"defect_statement_{pk}.docx")
    except ValueError as e:
        return Response({"error": str(e)}, status=400)


@swagger_auto_schema(
    method="post",
    operation_summary="Отправка в Telegram",
    operation_description="Отправляет уведомление в Telegram чат",
    responses={
        200: openapi.Response(
            "Success",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={"status": openapi.Schema(type=openapi.TYPE_STRING)},
            ),
        ),
        500: openapi.Response(
            "Server Error",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={"error": openapi.Schema(type=openapi.TYPE_STRING)},
            ),
        ),
    },
)
@api_view(["POST"])
def send_telegram_notification(request, pk):
    note = get_object_or_404(Note, pk=pk)
    service = TelegramNotificationService()
    success = service.send_notification(note)

    if success:
        return Response({"status": "Уведомление отправлено"})
    return Response({"error": "Ошибка отправки"}, status=500)


@login_required
@require_POST
@csrf_exempt  # Для упрощения, в production используйте правильную CSRF-защиту
def send_to_telegram_api(request, pk):
    try:
        statement = DefectStatement.objects.get(pk=pk)
        success = send_to_telegram(statement)

        return JsonResponse(
            {"success": success, "error": None if success else "Ошибка отправки"}
        )
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


# api = NinjaAPI(
#     title="Daily Planner API",
#     version="1.0.0",
#     description="API для управления заметками и дефектными ведомостями",
#     docs_decorator=login_required
# )
#
# # --- Схемы данных ---
# class UserOut(ModelSchema):
#     class Config:
#         model = User
#         model_fields = ['id', 'username', 'email']
#
# class NoteOut(ModelSchema):
#     user: UserOut
#     note_type_display: str = Field(None, alias='get_note_type_display')
#
#     class Config:
#         model = Note
#         model_fields = ['id', 'title', 'content', 'note_type',
#                        'created_at', 'object_name', 'address']
#
# class NoteIn(Schema):
#     title: str = Field(..., max_length=200, example="Заголовок заметки")
#     content: str = Field(..., example="Текст заметки...")
#     note_type: str = Field(..., enum=["personal", "work", "defect", "statement"])
#
# # --- Эндпоинты ---
# @api.post("/notes", response=NoteOut, summary="Создать заметку")
# def create_note(request, payload: NoteIn):
#     """Создание новой заметки с указанным типом"""
#     note = Note.objects.create(user=request.user, **payload.dict())
#     return note
#
# @api.get("/notes/{note_id}", response=NoteOut, summary="Получить заметку")
# def get_note(request, note_id: int):
#     """Получение детальной информации о заметке"""
#     return Note.objects.get(id=note_id)
#
# @api.get("/defect-statements/{id}/download", summary="Скачать дефектную ведомость", response={200: bytes, 403: None})
# def download_defect_statement(request, id: int):
#     # Ваша логика
#     file_path = "path/to/your/file.pdf"
#     return FileResponse(open(file_path, 'rb'), as_attachment=True, filename="defect_statement.pdf")
