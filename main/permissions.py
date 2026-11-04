from rest_framework.permissions import (
    BasePermission,
    SAFE_METHODS,
)
from rest_framework.request import HttpRequest

class IsPortfolioOwnerOrReadOnly(BasePermission):
    message = 'Only the portfolio owner can change awards.'

    def has_permission(self, request: HttpRequest, view):
        return request.method in SAFE_METHODS or request.user.is_superuser
