from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.views import TokenObtainPairView

from core.permissions import IsSuperAdmin
from .serializers import (
    ChangePasswordSerializer,
    EmailTokenObtainPairSerializer,
    AdminLoginSerializer,
    UserSerializer,
)


class EmailTokenObtainPairView(TokenObtainPairView):
    """
    JWT token endpoint for email-based authentication.
    Takes email and password and returns access and refresh tokens.
    """
    serializer_class = EmailTokenObtainPairSerializer


class AdminLoginView(TokenObtainPairView):
    """
    Admin panel login: email + password, returns JWT and user.
    Only users with is_staff=True can log in.
    Rate limited to reduce brute-force risk.
    """
    serializer_class = AdminLoginSerializer
    throttle_scope = 'admin_login'


class CurrentUserView(APIView):
    """
    GET / PATCH / PUT current authenticated user. Used by the admin profile page.

    Only safe profile fields (``name``, ``phone_number``) are writable — role,
    is_active, email, etc. stay read-only via ``UserSerializer.read_only_fields``.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    def patch(self, request):
        serializer = UserSerializer(
            request.user,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def put(self, request):
        return self.patch(request)


class ChangePasswordView(APIView):
    """
    POST /api/auth/change-password/

    Body: { "current_password": "...", "new_password": "..." }

    Verifies the current password, runs Django's configured password validators
    against the new one, and saves it. Returns a 200 with a success message.
    Validation errors are returned in the standard DRF shape, plus a top-level
    ``message`` string so the admin frontend can display it directly.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request},
        )
        if not serializer.is_valid():
            # Flatten the first error to a friendly top-level ``message`` for the UI,
            # while keeping the per-field errors available under ``errors``.
            first_message = None
            for field_errors in serializer.errors.values():
                if isinstance(field_errors, list) and field_errors:
                    first_message = str(field_errors[0])
                    break
                if isinstance(field_errors, str):
                    first_message = field_errors
                    break
            return Response(
                {
                    'message': first_message or 'Invalid password change request.',
                    'errors': serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save(update_fields=['password'])

        return Response(
            {'message': 'Password updated successfully.'},
            status=status.HTTP_200_OK,
        )


class LogoutView(APIView):
    """
    POST logout: accept optional refresh token in body, return success.
    Frontend clears tokens; optional server-side blacklist can be added later.
    """
    permission_classes = []  # Allow unauthenticated so frontend can call with refresh only

    def post(self, request):
        # Body may include { "refresh": "..." } for future blacklisting
        return Response(
            {'message': 'Successfully logged out.'},
            status=status.HTTP_200_OK,
        )


class UserCountAPIView(APIView):
    """
    GET user count for dashboard. Super admin only.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def get(self, request):
        User = get_user_model()
        count = User.objects.count()
        return Response({'count': count})
