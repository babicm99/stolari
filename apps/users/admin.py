from django.contrib import admin
from .models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'full_name', 'country', 'city', 'dark_mode')
    list_filter = ('role', 'dark_mode', 'country')
    search_fields = ('user__username', 'user__email', 'full_name', 'country', 'city')
    raw_id_fields = ('user',)
