# notes/templatetags/markdown_tags.py
import markdown as md  # Переименовываем импорт
from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter(name='apply_markdown')  # Изменяем имя фильтра
def apply_markdown(value):
    return mark_safe(md.markdown(value))  # Используем переименованный модуль
