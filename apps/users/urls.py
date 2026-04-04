from django.urls import path
from apps.users import views


urlpatterns = [
    path(
        'ajax/update-coefficient-preference/',
        views.update_coefficient_preference,
        name='update_coefficient_preference',
    ),
    path('profile/', views.profile, name='profile'),
    path('upload-avatar/', views.upload_avatar, name='upload_avatar'),
    path('change-password/', views.change_password, name='change_password'),
    path('change-mode/', views.change_mode, name='change_mode'),
]
