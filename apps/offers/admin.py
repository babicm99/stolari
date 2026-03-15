from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Offer, Element, ElementSubType, ElementSubTypeElements, CalculatedElementSubTypeElement, CoefficientGroup, Coefficient, OfferCoefficientSelection


@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    list_display = ('title', 'price', 'discount_percentage', 'is_active', 'start_date', 'end_date', 'created_at')
    list_filter = ('is_active', 'created_at', 'start_date', 'end_date')
    search_fields = ('title', 'description')
    readonly_fields = ('created_at', 'updated_at', 'created_by')
    fieldsets = (
        (_('Basic Information'), {
            'fields': ('title', 'description', 'price', 'discount_percentage')
        }),
        (_('Dates'), {
            'fields': ('start_date', 'end_date')
        }),
        (_('Status'), {
            'fields': ('is_active',)
        }),
        (_('Metadata'), {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change:  # If creating a new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(ElementSubType)
class ElementSubTypeAdmin(admin.ModelAdmin):
    list_display = ['code', 'type', 'name', 'image']
    list_filter = ['type']
    search_fields = ['name']
    fieldsets = (
        (None, {'fields': ('type', 'code', 'name')}),
        (_('Dimensions'), {'fields': ('Dx', 'Dy', 'Dz')}),
        (_('Image'), {'fields': ('image',)}),
        (_('Extra fields (Ladice etc.)'), {
            'fields': ('extra_fields_schema',),
            'description': _('JSON list of extra inputs shown when this sub-type is selected. '
                             'Example: [{"name": "broj_ladica", "label": "Broj ladiča", "type": "number", "required": true}]'),
        }),
    )


@admin.register(Element)
class ElementAdmin(admin.ModelAdmin):
    list_display = ['offer', 'element_type', 'sub_type', 'quantity', 'Dx', 'Dy', 'Dz', 'dubina_ladice', 'visina_fronte_1']
    list_filter = ['element_type']
    autocomplete_fields = ['sub_type']
    fieldsets = (
        (_('Basic Information'), {
            'fields': ('offer', 'element_type', 'sub_type', 'quantity')
        }),
        (_('Dimensions'), {
            'fields': ('Dx', 'Dy', 'Dz'),
            'classes': ('collapse',)
        }),
        (_('Ladice fields'), {
            'fields': ('dubina_ladice', 'visina_fronte_1', 'visina_fronte_2', 'visina_fronte_3', 'visina_fronte_4'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ElementSubTypeElements)
class ElementSubTypeElementsAdmin(admin.ModelAdmin):
    list_display = ['element_name', 'formula_code', 'element_sub_type', 'element_quantity', 'element_price', 'element_discount', 'element_total_price']
    list_filter = ['element_sub_type', 'element_sub_type__type', 'formula_code']
    search_fields = ['element_name', 'element_sub_type__code', 'element_sub_type__name', 'formula_code']
    fieldsets = (
        (_('Basic Information'), {
            'fields': ('element_name', 'element_sub_type', 'element_quantity')
        }),
        (_('Formula Configuration'), {
            'fields': ('formula_code',),
            'description': _('If formula_code is set, Dx and Dy will be calculated automatically when saving an offer. '
                          'The formula calculates both dimensions together. Only Dx and Dy are calculated (not Dz).')
        }),
        (_('Pricing'), {
            'fields': ('element_price', 'element_discount', 'element_total_price')
        }),
    )
    autocomplete_fields = ['element_sub_type']


@admin.register(CalculatedElementSubTypeElement)
class CalculatedElementSubTypeElementAdmin(admin.ModelAdmin):
    list_display = ['element_name', 'element', 'offer', 'Dx', 'Dy', 'element_quantity', 'calculated_at']
    list_filter = ['offer', 'element__element_type', 'calculated_at']
    search_fields = ['element_name', 'element__sub_type__code', 'offer__title']
    readonly_fields = ['calculated_at']
    fieldsets = (
        (_('Relations'), {
            'fields': ('offer', 'element', 'sub_type_element')
        }),
        (_('Calculated Dimensions'), {
            'fields': ('Dx', 'Dy')
        }),
        (_('Element Information'), {
            'fields': ('element_name', 'element_quantity', 'element_price', 'element_discount', 'element_total_price')
        }),
        (_('Metadata'), {
            'fields': ('calculated_at',),
            'classes': ('collapse',)
        }),
    )
    raw_id_fields = ['offer', 'element', 'sub_type_element']


@admin.register(CoefficientGroup)
class CoefficientGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'code')
    search_fields = ('name', 'code')


@admin.register(Coefficient)
class CoefficientAdmin(admin.ModelAdmin):
    list_display = ('name', 'group', 'code', 'value', 'is_default')
    list_filter = ('group', 'is_default')
    search_fields = ('name', 'code', 'group__name')
    raw_id_fields = ('group',)
    fieldsets = (
        ('Basic Information', {
            'fields': ('group', 'name', 'code', 'value')
        }),
        ('Default Settings', {
            'fields': ('is_default',),
            'description': 'If checked, this coefficient will be automatically selected for new offers. Only one coefficient per group should be marked as default.'
        }),
    )


@admin.register(OfferCoefficientSelection)
class OfferCoefficientSelectionAdmin(admin.ModelAdmin):
    list_display = ('offer', 'group', 'coefficient')
    list_filter = ('group',)
    search_fields = ('offer__title', 'group__name', 'coefficient__name')
    raw_id_fields = ('offer', 'group', 'coefficient')