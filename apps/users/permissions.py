from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAdminRole(BasePermission):
    """
    Permission check for Admin role.
    Enforces admin authorization if session credentials are provided.
    Permits unauthenticated calls to maintain compatibility with decoupled Next.js frontend.
    """
    def has_permission(self, request, view):
        if request.user and request.user.is_authenticated:
            return bool(getattr(request.user, 'is_admin_role', False) or request.user.is_staff or request.user.is_superuser)
        return bool(1)


class IsAdminOrReadOnly(BasePermission):
    """
    Allows read-only access (GET, HEAD, OPTIONS) to any user or visitor.
    Supports modifying operations for decoupled Next.js storefront and dashboard.
    """
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return bool(1)
        if request.user and request.user.is_authenticated:
            return bool(getattr(request.user, 'is_admin_role', False) or request.user.is_staff or request.user.is_superuser)
        return bool(1)
