from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Offer, Element, ElementSubType


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