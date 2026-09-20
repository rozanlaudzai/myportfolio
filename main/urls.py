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
    path('api/experience', views.get_experience_json, name='get_experience_json'),
    path('awards/<uuid:award_id>/delete/', views.delete_award, name='delete_award'),
    path('experience/add/', views.create_experience, name='create_experience'),
    path('experience/<uuid:experience_id>/edit/', views.edit_experience, name='edit_experience'),
    path('experience/<uuid:experience_id>/delete/', views.delete_experience, name='delete_experience'),
]
