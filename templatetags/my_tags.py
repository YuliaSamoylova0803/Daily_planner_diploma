from django import template
from django.conf import settings

register = template.Library()

@register.filter()
def media_filter(path):
    if path:
        return f"{settings.MEDIA_URL}{path}"
    return "#"


@register.filter
def filename(value):
    return value.split("/")[-1]
