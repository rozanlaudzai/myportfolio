from django.urls import path
from . import api_views

app_name = 'api'

urlpatterns = [
    path('experiences/', api_views.experience_list, name='experience-list'),
    path('experiences/<uuid:experience_id>/', api_views.experience_detail, name='experience-detail'),
    path('experiences/<uuid:experience_id>/star/', api_views.experience_star, name='experience-star'),
    path('awards/', api_views.award_list, name='award-list'),
    path('awards/<uuid:award_id>/', api_views.award_detail, name='award-detail'),
    path('awards/<uuid:award_id>/star/', api_views.award_star, name='award-star'),
]
