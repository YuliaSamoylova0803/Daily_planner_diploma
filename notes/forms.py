from django import forms
from .models import Note, NoteImage
from django.forms import BooleanField, DateInput


class StyleFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if isinstance(field, BooleanField):
                field.widget.attrs["class"] = "form-check-input"
            else:
                field.widget.attrs["class"] = field.widget.attrs.get("class", "") + " form-control"
            if field.help_text:
                field.widget.attrs["placeholder"] = field.help_text
            if isinstance(field.widget, forms.DateInput):
                field.widget.attrs["class"] = field.widget.attrs.get("class", "") + " datepicker"


class NoteImageForm(StyleFormMixin, forms.ModelForm):
    """
    Форма для загрузки изображений к записям.
    Используется в AddImagesView для дефектов и ведомостей.
    """
    class Meta:
        model = NoteImage
        fields = ['image', 'description']
        widgets = {
            'description': forms.TextInput(attrs={'placeholder': 'Описание изображения'}),
        }
        help_texts = {
            'image': 'Загрузите изображение дефекта',
            'description': 'Краткое описание (необязательно)',
        }


class BaseNoteForm(StyleFormMixin, forms.ModelForm):
    """
        Базовый класс формы для всех типов записей.
        Содержит только общие поля и функционал.

        Преимущества:
        1. Четкое разделение ответственности - каждая форма отвечает только за свой тип данных
        2. Невозможно случайно отправить невалидные данные для конкретного типа записи
        3. Проще в поддержке - изменения для одного типа не затрагивают другие
        4. Более безопасно - нет скрытых полей, которые могут быть подменены
    """
    class Meta:
        model = Note
        fields = ['title', 'content', 'image']
        widgets = {
            "content": forms.Textarea(attrs={"rows": 5}),
        }
        help_texts = {
            "title": "Введите заголовок записи",
            "content": "Подробное описание",
            "image": "Загрузите изображение (необязательно)",
        }


class PersonalNoteForm(BaseNoteForm):
    """
        Форма для личных записей. Добавляет специфичные поля:
        - mood (настроение)
        - is_private (приватность)

        Преимущества перед единой формой:
        1. Пользователь видит только релевантные поля
        2. Валидация происходит только для нужных полей
        3. Чище код - нет условий для скрытия/показа полей
    """
    class Meta(BaseNoteForm.Meta):
        fields = BaseNoteForm.Meta.fields + ['mood', 'is_private']
        widgets = {
            **BaseNoteForm.Meta.widgets,
            "is_private": forms.CheckboxInput(),
        }


class WorkNoteForm(BaseNoteForm):
    class Meta(BaseNoteForm.Meta):
        fields = BaseNoteForm.Meta.fields + ['object_name', 'address']


class DefectNoteForm(BaseNoteForm):
    class Meta(BaseNoteForm.Meta):
        fields = BaseNoteForm.Meta.fields + ['object_name', 'address']


class DefectStatementForm(BaseNoteForm):
    """
        Форма для дефектных ведомостей. Специфика:
        - Выбор связанных дефектов (defects)
        - Номер ведомости
        - Дата утверждения

        Особые преимущества:
        1. Автоматическая фильтрация дефектов (только note_type='defect')
        2. Специальные виджеты для полей дат
        3. Четкая структура без лишних полей
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['defects'].queryset = Note.objects.filter(note_type='defect')

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get('approval_date'):
            raise forms.ValidationError("Дата утверждения обязательна для дефектных ведомостей")
        return cleaned_data

    class Meta(BaseNoteForm.Meta):
        fields = BaseNoteForm.Meta.fields + [
            'object_name', 'address',
            'statement_number', 'approval_date', 'approved_by', 'defects'
        ]
        widgets = {
            **BaseNoteForm.Meta.widgets,
            "approval_date": DateInput(attrs={"type": "date"}),
            "defects": forms.SelectMultiple(attrs={'class': 'form-select'}),
        }
        help_texts = {
            **BaseNoteForm.Meta.help_texts,
            "defects": "Выберите дефекты для включения в ведомость",
        }


def get_note_form_class(note_type):
    """
        Фабрика форм, возвращающая нужный класс формы по типу записи.

        Параметры:
            note_type (str): Один из типов записей ('personal', 'work', 'defect', 'defect_statement')

        Возвращает:
            type[forms.ModelForm]: Класс формы для указанного типа записи

        Преимущества:
        1. Единая точка входа для создания форм
        2. Легко расширяется для новых типов записей
        3. Прозрачная логика выбора формы
    """
    forms_mapping = {
        'personal': PersonalNoteForm,
        'work': WorkNoteForm,
        'defect': DefectNoteForm,
        'defect_statement': DefectStatementForm,
    }
    return forms_mapping.get(note_type, BaseNoteForm)

