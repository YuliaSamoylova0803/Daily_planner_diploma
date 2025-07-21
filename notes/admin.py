from django.contrib import admin
from .models import Note, DefectImage

# Register your models here.
admin.site.register(Note)

@admin.register(DefectImage)
class DefectImageAdmin(admin.ModelAdmin):
    list_display = ('id', 'note', 'defect_number', 'description')
    list_filter = ('note', 'defect_number')
    search_fields = ('description', 'note__title')
