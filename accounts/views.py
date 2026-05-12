from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.views import TokenObtainPairView

from core.permissions import IsSuperAdmin
from .serializers import (
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
    GET current authenticated user (for JWT). Used by admin frontend.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


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
