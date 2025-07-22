from django import forms
from .models import Note
from django.forms import BooleanField


class StyleFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for fild_name, field in self.fields.items():
            if isinstance(field, BooleanField):
                field.widget.attrs["class"] = "form-check-input"
            else:
                field.widget.attrs["class"] = "form-control"
            # Добавляем placeholder
            if field.help_text:
                field.widget.attrs["placeholder"] = field.help_text
            # Для полей даты добавляем специальный класс
            if isinstance(field.widget, forms.DateInput):
                field.widget.attrs["class"] += " datepicker"


class NoteForm(StyleFormMixin, forms.ModelForm):
    class Meta:
        model = Note
        fields = [
            'note_type', 'title', 'content', 'image',
            'mood', 'is_private',
            'object_name', 'contractor', 'customer', 'document', 'address',
            'act_number', 'inspection_date',
            'statement_number', 'approval_date', 'approved_by'
        ]
        widgets = {
            "content": forms.Textarea(attrs={"rows": 5}),
            "inspection_date": forms.DateInput(attrs={"type": "date"}),
            "approval_date": forms.DateInput(attrs={"type": "dte"}),
            "is_private": forms.CheckboxInput(),
        }
        help_texts = {
            "title": "Введите заголовок записи",
            "context": "Подробное описание",
            "image": "Загрузите изображение (необязательно)",
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Определяем тип записи
        note_type = self.instance.note_type if self.instance.pk else self.data.get("note_type", None)

        # Скрываем неиспользуемые поля
        self._hide_unused_fields(note_type)

        # Добавляем специфичные классы для разных полей
        self.fields['content'].widget.attrs['class'] += ' summernote'
        self.fields['is_private'].widget.attrs['class'] = 'form-check-input'

    def _hide_unused_fields(self, note_type):
        """Скрываем поля в зависимости от типа записи"""
        field_rules = {
            'personal': ['mood', 'is_private'],
            'hidden_act': ['act_number', 'inspection_date'],
            'defect_statement': [
                'statement_number', 'approval_date',
                'approved_by', 'address'
            ],
            'work': ['object_name', 'contractor', 'customer']
        }

        for note_type_pattern, fields_to_show in field_rules.items():
            for field_name, field in self.fields.items():
                if note_type_pattern != note_type and field_name not in fields_to_show:
                    if field_name not in ["note_type", "title", "content", "image"]:
                        field.widget = forms.HiddenInput()
