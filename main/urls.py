from django.urls import path
from . import views

app_name = 'main'

urlpatterns = [
    path('', views.index, name='index'),
    path('experience/', views.show_experience, name='show_experience'),
]
