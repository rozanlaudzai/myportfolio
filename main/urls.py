from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('experience', views.show_experience, name='experience'),
]
