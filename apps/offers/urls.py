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
    path('ajax/get-subtype-elements/', views.get_subtype_elements, name='get_subtype_elements'),
    path('ajax/update-coefficient/', views.update_coefficient, name='update_coefficient'),
    path('ajax/update-element-dimensions/', views.update_element_dimensions, name='update_element_dimensions'),
    path('ajax/auto-save-offer/', views.auto_save_offer, name='auto_save_offer'),
    path('ajax/recalculate-dimensions/<int:pk>/', views.recalculate_dimensions, name='recalculate_dimensions'),
]


