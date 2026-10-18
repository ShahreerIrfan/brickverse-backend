from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAdminRole(BasePermission):
    """
    Permission check for Admin role.
    Strictly permits only authenticated users with Admin role, staff, or superuser status.
    Rejects anonymous or regular customer requests (401/403).
    """
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            (getattr(request.user, 'is_admin_role', False) or request.user.is_staff or request.user.is_superuser)
        )


class IsAdminOrReadOnly(BasePermission):
    """
    Allows read-only access (GET, HEAD, OPTIONS) to any user or visitor.
    Requires authenticated Admin role for any modifying operations (POST, PUT, PATCH, DELETE).
    """
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return bool(request.method in SAFE_METHODS)
        return bool(
            request.user and
            request.user.is_authenticated and
            (getattr(request.user, 'is_admin_role', False) or request.user.is_staff or request.user.is_superuser)
        )
