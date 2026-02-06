from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Offer, Element, ElementSubType, ElementSubTypeElements, CoefficientGroup, Coefficient, OfferCoefficientSelection


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


@admin.register(Element)
class ElementAdmin(admin.ModelAdmin):
    list_display = ['offer', 'element_type', 'sub_type', 'quantity']
    list_filter = ['element_type']
    autocomplete_fields = ['sub_type']


@admin.register(ElementSubTypeElements)
class ElementSubTypeElementsAdmin(admin.ModelAdmin):
    list_display = ['element_name', 'element_sub_type', 'element_quantity', 'element_price', 'element_discount', 'element_total_price']
    list_filter = ['element_sub_type', 'element_sub_type__type']
    search_fields = ['element_name', 'element_sub_type__code', 'element_sub_type__name']
    fieldsets = (
        (_('Basic Information'), {
            'fields': ('element_name', 'element_sub_type', 'element_quantity')
        }),
        (_('Pricing'), {
            'fields': ('element_price', 'element_discount', 'element_total_price')
        }),
        (_('Dimensions'), {
            'fields': ('Dx', 'Dy', 'Dz'),
            'classes': ('collapse',)
        }),
    )
    autocomplete_fields = ['element_sub_type']


@admin.register(CoefficientGroup)
class CoefficientGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'code')
    search_fields = ('name', 'code')


@admin.register(Coefficient)
class CoefficientAdmin(admin.ModelAdmin):
    list_display = ('name', 'group', 'code', 'value')
    list_filter = ('group',)
    search_fields = ('name', 'code', 'group__name')
    raw_id_fields = ('group',)


@admin.register(OfferCoefficientSelection)
class OfferCoefficientSelectionAdmin(admin.ModelAdmin):
    list_display = ('offer', 'group', 'coefficient')
    list_filter = ('group',)
    search_fields = ('offer__title', 'group__name', 'coefficient__name')
    raw_id_fields = ('offer', 'group', 'coefficient')