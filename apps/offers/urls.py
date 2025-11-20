from django.urls import path
from . import views

app_name = 'offers'

urlpatterns = [
    path('', views.offers_list, name='list'),
    path('create/', views.offer_create, name='create'),
    path('detail/<int:pk>/', views.offer_detail, name='detail'),
    path('edit/<int:pk>/', views.offer_edit, name='edit'),
    path('delete/<int:pk>/', views.offer_delete, name='delete'),
    path('ajax/get-subtypes/', views.get_subtypes, name='get_subtypes'),
]


