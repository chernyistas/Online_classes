from rest_framework import permissions

from users.models import User


class IsModer(permissions.BasePermission):
    """Проверяет, является ли пользователь модератором"""

    def has_permission(self, request, view):
        return request.user.groups.filter(name="moderators").exists()


class IsOwner(permissions.BasePermission):
    """Проверяет, является ли пользователь владельцем"""

    def has_object_permission(self, request, view, obj):
        if isinstance(obj, User):
            return obj == request.user
        if hasattr(obj, "owner"):
            return obj.owner == request.user
        return False
