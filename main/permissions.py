from rest_framework.permissions import (
    BasePermission,
    SAFE_METHODS,
)
from rest_framework.request import HttpRequest

class IsPortfolioOwnerOrReadOnly(BasePermission):
    message = 'Only the portfolio owner can change awards.'

    def has_permission(self, request: HttpRequest, view):
        return request.method in SAFE_METHODS or request.user.is_superuser


class IsPortfolioOwnerOrEditorOrReadOnly(IsPortfolioOwnerOrReadOnly):
    message = 'Only the owner can create/delete awards; Editors may update them.'

    def has_permission(self, request: HttpRequest, view):
        if super().has_permission(request, view):
            return True
        return (
            request.user.is_authenticated
            and request.method in ('PUT', 'PATCH')
            and request.user.groups.filter(name='Editor').exists()
        )
