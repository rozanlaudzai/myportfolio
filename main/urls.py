from django.urls import path
from . import views

app_name = 'main'

urlpatterns = [
    path('', views.index, name='index'),
    path('experience/', views.show_experience, name='show_experience'),
    path('awards/', views.show_awards, name='show_awards'),
    path('awards/add/', views.create_award, name='create_award'),
    path('awards/<uuid:award_id>/edit/', views.edit_award, name='edit_award'),
    path('api/awards', views.get_awards_json, name='get_awards_json'),
    path('awards/<uuid:award_id>/delete/', views.delete_award, name='delete_award'),
]
