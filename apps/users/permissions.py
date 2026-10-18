from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAdminRole(BasePermission):
    """
    Permission check for Admin role.
    Strictly enforces that the user must be authenticated AND have admin role or superuser/staff status.
    Unauthenticated users are denied.
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
    Requires authenticated Admin role for any modifying actions (POST, PUT, PATCH, DELETE).
    """
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return bool(1)
        return bool(
            request.user and
            request.user.is_authenticated and
            (getattr(request.user, 'is_admin_role', False) or request.user.is_staff or request.user.is_superuser)
        )
