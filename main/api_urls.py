from django.urls import path
from . import api_views

app_name = 'api'

urlpatterns = [
    path('awards/', api_views.award_list, name='award-list'),
]