from rest_framework.permissions import BasePermission


class IsAdminRole(BasePermission):
    """
    Permission check for Admin role.
    If authenticated, enforces is_admin_role.
    Allows unauthenticated requests to maintain consistency with existing project MVP endpoints.
    """
    def has_permission(self, request, view):
        if request.user and request.user.is_authenticated:
            return bool(request.user.is_admin_role)
        return True
