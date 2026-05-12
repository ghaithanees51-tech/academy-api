from django.db import transaction
from django.db.models import Sum
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import InvalidToken

from core.permissions import IsSuperAdmin
from .authentication import CodeJWTAuthentication
from .models import AuthCode, AuthCodeUsage
from .serializers import (
    AuthCodeCreateSerializer,
    AuthCodeSerializer,
    CodeLoginSerializer,
)
from .tokens import CodeAccessToken


def get_client_ip(request):
    """
    Get the client's IP address from the request.
    Handles proxies and forwarded requests.
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


class AuthCodeViewSet(viewsets.ModelViewSet):
    """
    Admin viewset for managing authentication codes.
    Only super admins can access these endpoints.
    """
    queryset = AuthCode.objects.select_related('created_by').all()
    permission_classes = [IsSuperAdmin]

    def get_serializer_class(self):
        if self.action == 'create':
            return AuthCodeCreateSerializer
        return AuthCodeSerializer

    def perform_create(self, serializer):
        """
        Set the created_by field to the current user.
        """
        serializer.save(created_by=self.request.user)

    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request):
        """
        GET /api/admin/auth-codes/stats/
        Returns total auth codes count and total used count (sum of used_count).
        """
        total_count = AuthCode.objects.count()
        used_count_result = AuthCode.objects.aggregate(total=Sum('used_count'))
        used_count = used_count_result['total'] or 0
        return Response({
            'total_count': total_count,
            'used_count': used_count,
        })

    @action(detail=True, methods=['post'])
    def revoke(self, request, pk=None):
        """
        Revoke an authentication code.
        POST /api/admin/auth-codes/{id}/revoke/
        """
        auth_code = self.get_object()

        if auth_code.status == 'revoked':
            return Response(
                {'detail': 'Code is already revoked.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        auth_code.revoke()

        serializer = self.get_serializer(auth_code)
        return Response(serializer.data)


@method_decorator(csrf_exempt, name='dispatch')
class CodeLoginAPIView(APIView):
    """
    Public endpoint for code-based authentication.
    POST /api/public/code-login/
    Body: { "code": "12345678" }
    Returns: JWT token with code claims
    """
    authentication_classes = []  # No authentication required for login
    permission_classes = [AllowAny]
    throttle_scope = 'code_login'

    def post(self, request):
        serializer = CodeLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        code_value = serializer.validated_data['code']

        try:
            # Use select_for_update to prevent race conditions
            with transaction.atomic():
                auth_code = AuthCode.objects.select_for_update().get(
                    code=code_value
                )

                # Validate code - only check if active
                if auth_code.status != 'active':
                    raise AuthCode.DoesNotExist

                # Get client IP address
                ip_address = get_client_ip(request)
                user_agent = request.META.get('HTTP_USER_AGENT', '')

                # Track this usage with IP address
                AuthCodeUsage.objects.create(
                    auth_code=auth_code,
                    ip_address=ip_address,
                    user_agent=user_agent
                )

                # Increment usage count and update last used time
                auth_code.used_count += 1
                auth_code.last_used_at = timezone.now()
                auth_code.save(update_fields=['used_count', 'last_used_at', 'updated_at'])

        except AuthCode.DoesNotExist:
            # Generic error message to avoid leaking information
            return Response(
                {'detail': 'Invalid authentication code.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Generate JWT token
        token = CodeAccessToken.for_auth_code(auth_code)

        return Response({
            'access': str(token),
            'token_type': 'code',
            'expires_in': int(CodeAccessToken.lifetime.total_seconds()),
        }, status=status.HTTP_200_OK)


class CodeMeAPIView(APIView):
    """
    Public endpoint to get current code token information.
    GET /api/public/code-me/
    Requires: Authorization header with code JWT token
    Returns: { "token_type": "code", "code_id": ... }
    """
    authentication_classes = [CodeJWTAuthentication]
    permission_classes = []  # Will validate token type manually

    def get(self, request):
        # Validate that this is a code token
        try:
            token = request.auth
            if not token or token.get('token_type') != 'code':
                raise InvalidToken('This endpoint requires a code-based token.')

            return Response({
                'token_type': 'code',
                'code_id': token.get('code_id'),
            })

        except (InvalidToken, AttributeError) as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_401_UNAUTHORIZED
            )
