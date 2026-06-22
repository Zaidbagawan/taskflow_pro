from rest_framework.permissions import BasePermission, SAFE_METHODS


#  admin Only
class Isadmin(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'admin'


#  User Only
class IsUser(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'user'


#  Task Owner (Object-Level)
class IsTaskOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        #  Owner OR Admin
        return (
            obj.assigned_to == request.user
            or request.user.role == "admin"
        )


#  Manager or Admin
class IsManagerOrAdmin(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role in ['manager', 'admin']
        )


#  Read Only or Owner
class IsOwnerOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        # Allow safe methods (GET, HEAD, OPTIONS)
        if request.method in SAFE_METHODS:
            return True

        return request.user and obj.assigned_to == request.user