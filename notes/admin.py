from django.contrib import admin
from .models import Note, NoteImage

# Register your models here.
admin.site.register(Note)

@admin.register(NoteImage)
class NoteImageAdmin(admin.ModelAdmin):
    list_display = ('id', 'note', 'description')
    list_filter = ('note',)
    search_fields = ('description', 'note__title')
