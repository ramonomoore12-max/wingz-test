from rest_framework.permissions import BasePermission


class IsAdminRole(BasePermission):
    """
    Grants access only to authenticated users with role='admin'.
    """

    message = 'Access restricted to admin users only.'

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and getattr(user, 'role', None) == 'admin')
