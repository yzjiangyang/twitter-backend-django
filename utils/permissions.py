from rest_framework.permissions import BasePermission


class IsObjectOwner(BasePermission):
    message = 'You do not have permissions to access this object.'

    # only trigger this function when detail = False
    def has_permission(self, request, view):
        return True

    # trigger both when detail = True
    def has_object_permission(self, request, view, obj):
        # obj is retrieved from self.get_object()
        return request.user == obj.user