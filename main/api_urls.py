from django.urls import path
from rest_framework.authtoken.views import obtain_auth_token
from . import api_views

app_name = 'api'

urlpatterns = [
    path('auth/token/', obtain_auth_token, name='api_token_auth'),
    path('auth/logout/', api_views.api_logout, name='api_logout'),

    # experience
    path('experiences/', api_views.experience_list, name='experience-list'),
    path('experiences/<uuid:experience_id>/', api_views.experience_detail, name='experience-detail'),
    path('experiences/<uuid:experience_id>/star/', api_views.experience_star, name='experience-star'),

    # award
    path('awards/', api_views.award_list, name='award-list'),
    path('awards/<uuid:award_id>/', api_views.award_detail, name='award-detail'),
    path('awards/<uuid:award_id>/star/', api_views.award_star, name='award-star'),

    # project
    path('projects/', api_views.project_list, name='project-list'),
    path('projects/<uuid:project_id>/', api_views.project_detail, name='project-detail'),
    path('projects/<uuid:project_id>/star/', api_views.project_star, name='project-star'),
    
]
