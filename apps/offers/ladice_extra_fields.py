"""
Extra input fields for Element type "Ladice", by sub-type code.
- Code is used for mapping (e.g. LADICE_1, LADICE_2) — set ElementSubType.code in DB.
- Name is displayed in the UI to the user (e.g. "LADICE 1", "LADICE 2") — set ElementSubType.name in DB.
"""

# Shared field definitions (reused across sub-types)
DUBINA_LADICE = {
    'name': 'dubina_ladice',
    'label': 'DUBINA LADICE',
    'type': 'number',
    'required': True,
}

VISINA_FRONTE_1 = {
    'name': 'visina_fronte_1',
    'label': 'VISINA 1. FRONTE',
    'type': 'number',
    'required': True,
}

VISINA_FRONTE_2 = {
    'name': 'visina_fronte_2',
    'label': 'VISINA 2. FRONTE',
    'type': 'number',
    'required': True,
}

VISINA_FRONTE_3 = {
    'name': 'visina_fronte_3',
    'label': 'VISINA 3. FRONTE',
    'type': 'number',
    'required': True,
}

VISINA_FRONTE_4 = {
    'name': 'visina_fronte_4',
    'label': 'VISINA 4. FRONTE',
    'type': 'number',
    'required': True,
}

# Mapping: sub_type.code -> list of extra field definitions for the offer form.
# In DB use code = LADICE_1, LADICE_2, ... and name = "LADICE 1", "LADICE 2", ... (name is shown in UI).
LADICE_EXTRA_FIELDS_BY_SUBTYPE_CODE = {
    'LADICE_1': [
        DUBINA_LADICE,
        VISINA_FRONTE_1,
    ],
    'LADICE_2': [
        DUBINA_LADICE,
        VISINA_FRONTE_1,
    ],
    'LADICE_3': [
        DUBINA_LADICE,
        VISINA_FRONTE_1,
        VISINA_FRONTE_2,
    ],
    'LADICE_4': [
        DUBINA_LADICE,
        VISINA_FRONTE_1,
        VISINA_FRONTE_2,
        VISINA_FRONTE_3,
        VISINA_FRONTE_4,
    ],
}


# All Ladice field names on Element model (for saving from POST)
LADICE_FIELD_NAMES = ('dubina_ladice', 'visina_fronte_1', 'visina_fronte_2', 'visina_fronte_3', 'visina_fronte_4')


def get_ladice_extra_fields_for_sub_type(sub_type):
    """
    Return the list of extra field definitions for a Ladice ElementSubType.
    Matching is by sub_type.code (e.g. LADICE_1, LADICE_2). Name is only for UI display.
    """
    if sub_type.type != 'ladice':
        return None
    schema = LADICE_EXTRA_FIELDS_BY_SUBTYPE_CODE.get(sub_type.code)
    if schema is not None:
        return list(schema)
    return []
