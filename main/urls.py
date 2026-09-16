from django.urls import path
from . import views

app_name = 'main'

urlpatterns = [
    path('', views.index, name='index'),
    path('experience/', views.show_experience, name='show_experience'),
    path('awards/', views.show_awards, name='show_awards'),
    path('awards/add/', views.create_award, name='create_award'),
]
