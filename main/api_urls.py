from django.urls import path
from . import api_views

app_name = 'api'

urlpatterns = [
    path('awards/', api_views.award_list, name='award-list'),
    path('awards/<uuid:award_id>/', api_views.award_detail, name='award-detail'),
    path('awards/<uuid:award_id>/star/', api_views.award_star, name='award-star'),
]