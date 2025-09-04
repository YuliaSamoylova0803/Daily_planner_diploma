"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from notes.views import NoteViewSet, DefectStatementViewSet
from django.views.generic import TemplateView
from notes.api import generate_statement, send_telegram_notification
from django.conf import settings
from django.conf.urls.static import static


# Создаем router для DRF
router = DefaultRouter()
router.register(r"notes", NoteViewSet, basename="note")
router.register(
    r"defect-statements", DefectStatementViewSet, basename="defectstatement"
)

# Настройки Swagger/OpenAPI
schema_view = get_schema_view(
    openapi.Info(
        title="Daily Planner API",
        default_version="v1",
        description="API для управления заметками и дефектными ведомостями",
        contact=openapi.Contact(email="your@email.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include(router.urls)),
    path(
        "api/notes/<int:pk>/generate-statement/",
        generate_statement,
        name="generate-statement",
    ),
    path(
        "api/notes/<int:pk>/send-telegram/",
        send_telegram_notification,
        name="send-telegram",
    ),
    # Документация
    path(
        "swagger/",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
    path("redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
    path(
        "docs/",
        TemplateView.as_view(
            template_name="docs/index.html", extra_context={"api_url": "/api/docs"}
        ),
        name="docs",
    ),
    path("users/", include("users.urls", namespace="users")),
    path("", include("notes.urls", namespace="notes")),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(
        settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0]
    )
