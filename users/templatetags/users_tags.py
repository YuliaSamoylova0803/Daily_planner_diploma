from django import template
from django.conf import settings

register = template.Library()


@register.filter(name="media_filter")  # Явно задаем имя фильтра
def media_filter(path):
    if path:
        return f"{settings.MEDIA_URL}{path}"
    return "#"


@register.filter(name="filename")  # Явно задаем имя фильтра
def filename(value):
    return value.split("/")[-1] if value else ""
