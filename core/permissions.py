from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework_simplejwt.exceptions import InvalidToken


class IsSuperAdmin(BasePermission):
    """
    Permission class that allows access only to super admins.
    Checks both is_superuser flag and role='super_admin'.
    """

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            (request.user.is_superuser or request.user.role == 'super_admin')
        )


class CodeScopePermission(BasePermission):
    """
    Permission class for code-based authentication.
    Validates that:
    1. Token type is 'code'
    2. Token scope matches view's required_scope attribute
    3. If resource_id is set in token and view uses route param, they match
    
    Super admin tokens bypass this check.
    
    Usage in view:
        class MyView(APIView):
            permission_classes = [CodeScopePermission]
            required_scope = 'VIEW_REPORT'
    """

    def has_permission(self, request, view):
        # Super admins bypass code scope checks
        if request.user and request.user.is_authenticated:
            if hasattr(request.user, 'is_super_admin') and request.user.is_super_admin:
                return True

        # Check if token exists
        if not request.auth:
            return False

        # Validate token type
        try:
            token_type = request.auth.get('token_type')
            if token_type != 'code':
                return False
        except (AttributeError, InvalidToken):
            return False

        # Check if view has required_scope attribute
        if not hasattr(view, 'required_scope'):
            # If view doesn't specify scope, deny access for safety
            return False

        # Validate scope matches
        token_scope = request.auth.get('scope')
        if token_scope != view.required_scope:
            return False

        return True

    def has_object_permission(self, request, view, obj):
        # Super admins bypass code scope checks
        if request.user and request.user.is_authenticated:
            if hasattr(request.user, 'is_super_admin') and request.user.is_super_admin:
                return True

        # If no resource_id in token, allow (general scope access)
        token_resource_id = request.auth.get('resource_id')
        if not token_resource_id:
            return True

        # If view has resource ID parameter, validate it matches
        view_resource_id = None

        # Try to get resource_id from view kwargs (common DRF pattern)
        if hasattr(view, 'kwargs') and 'pk' in view.kwargs:
            view_resource_id = str(view.kwargs['pk'])
        elif hasattr(view, 'kwargs') and 'id' in view.kwargs:
            view_resource_id = str(view.kwargs['id'])
        elif hasattr(obj, 'id'):
            view_resource_id = str(obj.id)
        elif hasattr(obj, 'pk'):
            view_resource_id = str(obj.pk)

        # If we found a resource ID, validate it matches
        if view_resource_id:
            return str(token_resource_id) == view_resource_id

        # If no resource ID found in view, allow (can't validate)
        return True


class IsAuthenticatedCodeUser(BasePermission):
    """
    Permission class that allows access to any authenticated user with a valid JWT token.
    This includes both code-based authentication and admin users.
    """

    def has_permission(self, request, view):
        # Check if user is authenticated (has valid JWT token)
        return request.user and request.user.is_authenticated
