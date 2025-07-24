from django.contrib import admin
from django.utils.safestring import mark_safe

from .models import Note, DefectImage, DefectInStatement, DefectStatement

# Register your models here.
admin.site.register(Note)

@admin.register(DefectImage)
class DefectImageAdmin(admin.ModelAdmin):
    list_display = ['id', 'get_defect', 'image_preview']
    readonly_fields = ['image_preview']
    list_select_related = ['defect']  # Оптимизация запросов

    def get_defect(self, obj):
        return obj.defect.title if obj.defect else "-"
    get_defect.short_description = 'Дефект'
    get_defect.admin_order_field = 'defect__title'

    def image_preview(self, obj):
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" style="max-height: 100px;" />')
        return "-"
    image_preview.short_description = 'Превью'

class DefectInStatementInline(admin.TabularInline):
    model = DefectInStatement
    extra = 1

@admin.register(DefectStatement)
class DefectStatementAdmin(admin.ModelAdmin):
    list_display = ('statement_number', 'title', 'author', 'created_at')
    list_filter = ('author', 'created_at')
    search_fields = ('statement_number', 'title')
    inlines = [DefectInStatementInline]