from django import template

register = template.Library()

@register.filter
def get_note_icon(note_type):
    icons = {
        'personal': 'user',
        'work': 'briefcase',
        'defect_statement': 'file-alt',
        'hidden_act': 'file-signature'
    }
    return icons.get(note_type, 'sticky-note')
