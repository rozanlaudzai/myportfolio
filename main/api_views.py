from django.shortcuts import get_object_or_404
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status

from .models import Award
from .serializers import AwardSerializer
from .permissions import IsPortfolioOwnerOrReadOnly

@api_view(['GET', 'HEAD', 'POST'])
@authentication_classes([SessionAuthentication])
@permission_classes([IsPortfolioOwnerOrReadOnly])
def award_list(request: Request):
    if request.method in ('GET', 'HEAD'):
        awards = Award.objects.prefetch_related('starred_by').order_by('title', 'id')
        title = request.query_params.get('title', '').strip()

        if title:
            awards = awards.objects.filter(title__icontains=title)

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
@permission_classes([IsPortfolioOwnerOrReadOnly])
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
