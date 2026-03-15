import json
from django import template

register = template.Library()

# Ladice explicit field names on Element (for initial values when editing)
LADICE_FIELD_NAMES = ('dubina_ladice', 'visina_fronte_1', 'visina_fronte_2', 'visina_fronte_3', 'visina_fronte_4')


@register.filter
def to_json(value):
    """Serialize value to JSON string for use in HTML data attributes or hidden inputs."""
    if value is None:
        return '{}'
    try:
        return json.dumps(value)
    except (TypeError, ValueError):
        return '{}'


@register.filter
def ladice_initial_json(element):
    """Return JSON of Ladice explicit field values for an Element (for form initial values)."""
    if element is None:
        return '{}'
    data = {}
    for name in LADICE_FIELD_NAMES:
        val = getattr(element, name, None)
        data[name] = str(val) if val is not None else ''
    return json.dumps(data)
