from django.shortcuts import get_object_or_404
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import (
    Request,
    HttpRequest,
)
from rest_framework.response import Response
from rest_framework import status

from .models import (
    Award,
    Experience,
    Project,
)
from .serializers import (
    AwardSerializer,
    ExperienceSerializer,
    ProjectSerializer,
)
from .permissions import (
    IsPortfolioOwnerOrReadOnly,
    IsPortfolioOwnerOrEditorOrReadOnly,
)


@api_view(['GET', 'HEAD', 'POST'])
@authentication_classes([SessionAuthentication])
@permission_classes([IsPortfolioOwnerOrEditorOrReadOnly])
def award_list(request: Request):
    if request.method in ('GET', 'HEAD'):
        awards = Award.objects.prefetch_related('starred_by').order_by('-awarded_at', 'title', 'id')
        title = request.query_params.get('title', '').strip()

        if title:
            awards = awards.filter(title__icontains=title)

        serializer = AwardSerializer(awards, many=True, context={
            'request': request,
        })
        
        return Response(serializer.data)

    serializer = AwardSerializer(data=request.data, context={
        'request': request,
    })
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET', 'HEAD', 'PUT', 'PATCH', 'DELETE'])
@authentication_classes([SessionAuthentication])
@permission_classes([IsPortfolioOwnerOrEditorOrReadOnly])
def award_detail(request: Request, award_id):
    award = get_object_or_404(
        Award.objects.prefetch_related('starred_by'),
        pk=award_id,
    )

    if request.method in ('GET', 'HEAD'):
        serializer = AwardSerializer(award, context={
            'request': request,
        })
        return Response(serializer.data)

    if request.method == 'DELETE':
        award.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    serializer = AwardSerializer(
        award,
        data=request.data,
        partial=request.method == 'PATCH',
        context={
            'request': request,
        },
    )

    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data)


@api_view(['POST'])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def award_star(request: Request, award_id):
    award = get_object_or_404(Award, pk=award_id)
    
    if award.starred_by.filter(pk=request.user.pk).exists():
        award.starred_by.remove(request.user)
    else:
        award.starred_by.add(request.user)

    serializer = AwardSerializer(award, context={
        'request': request,
    })

    return Response(serializer.data)


@api_view(['GET', 'HEAD', 'POST'])
@authentication_classes([SessionAuthentication])
@permission_classes([IsPortfolioOwnerOrEditorOrReadOnly])
def experience_list(request: Request):
    if request.method in ('GET', 'HEAD'):
        experiences = Experience.objects.prefetch_related('starred_by', 'skills').order_by('-started_at', 'title', 'id')
        title = request.query_params.get('title', '').strip()

        if title:
            experiences = experiences.filter(title__icontains=title)

        serializer = ExperienceSerializer(experiences, many=True, context={
            'request': request,
        })
        
        return Response(serializer.data)

    serializer = ExperienceSerializer(data=request.data, context={
        'request': request,
    })
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET', 'HEAD', 'PUT', 'PATCH', 'DELETE'])
@authentication_classes([SessionAuthentication])
@permission_classes([IsPortfolioOwnerOrEditorOrReadOnly])
def experience_detail(request: Request, experience_id):
    experience = get_object_or_404(
        Experience.objects.prefetch_related('starred_by', 'skills'),
        pk=experience_id,
    )

    if request.method in ('GET', 'HEAD'):
        serializer = ExperienceSerializer(experience, context={
            'request': request,
        })
        return Response(serializer.data)

    if request.method == 'DELETE':
        experience.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    serializer = ExperienceSerializer(
        experience,
        data=request.data,
        partial=request.method == 'PATCH',
        context={
            'request': request,
        },
    )

    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data)


@api_view(['POST'])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def experience_star(request: Request, experience_id):
    experience = get_object_or_404(Experience, pk=experience_id)
    
    if experience.starred_by.filter(pk=request.user.pk).exists():
        experience.starred_by.remove(request.user)
    else:
        experience.starred_by.add(request.user)

    serializer = ExperienceSerializer(experience, context={
        'request': request,
    })

    return Response(serializer.data)


@api_view(['GET', 'HEAD', 'POST'])
@authentication_classes([SessionAuthentication])
@permission_classes([IsPortfolioOwnerOrReadOnly])
def project_list(request: Request):
    if request.method in ('GET', 'HEAD'):
        projects = Project.objects.prefetch_related('starred_by').order_by('title', 'id')
        title = request.query_params.get('title', '').strip()
        if title:
            projects = projects.filter(title__icontains=title)
        serializer = ProjectSerializer(
            projects,
            many=True,
            context={'request': request}
        )
        return Response(serializer.data)

    serializer = ProjectSerializer(
        data=request.data,
        context={'request': request}
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET', 'HEAD', 'PUT', 'PATCH', 'DELETE'])
@authentication_classes([SessionAuthentication])
@permission_classes([IsPortfolioOwnerOrReadOnly])
def project_detail(request: HttpRequest, project_id):
    project = get_object_or_404(
        Project.objects.prefetch_related('starred_by'),
        pk=project_id
    )

    if request.method in ('GET', 'HEAD'):
        serializer = ProjectSerializer(project, context={'request': request})
        return Response(serializer.data)

    if request.method == 'DELETE':
        project.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    serializer = ProjectSerializer(
        project,
        data=request.data,
        partial=request.method == 'PATCH',
        context={'request': request},
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data)


@api_view(['POST'])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def project_star(request: HttpRequest, project_id):
    project = get_object_or_404(
        Project,
        pk=project_id,
    )

    if project.starred_by.filter(pk=request.user.pk).exists():
        project.starred_by.remove(request.user)
    else:
        project.starred_by.add(request.user)

    serializer = ProjectSerializer(project, context={'request': request})
    return Response(serializer.data)



