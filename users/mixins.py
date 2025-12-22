from django.core.exceptions import PermissionDenied
from django.contrib.auth.mixins import AccessMixin
from users.models import User


class StaffOrAboveRequiredMixin(AccessMixin):
    """
    Mixin to restrict access to Super Admin, Owner, and Manager roles only.
    """
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        if not request.user.is_staff_or_above():
            raise PermissionDenied("You don't have permission to access this page.")
        
        return super().dispatch(request, *args, **kwargs)


class SuperAdminOrOwnerRequiredMixin(AccessMixin):
    """
    Mixin to restrict access to Super Admin and Owner roles only.
    """
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        if not (request.user.is_super_admin() or request.user.is_owner()):
            raise PermissionDenied("You don't have permission to access this page.")
        
        return super().dispatch(request, *args, **kwargs)

