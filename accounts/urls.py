from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    ChangePasswordView,
    EmailTokenObtainPairView,
    AdminLoginView,
    CurrentUserView,
    LogoutView,
    UserCountAPIView,
)

app_name = 'accounts'

urlpatterns = [
    path('login/', EmailTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('login/admin/', AdminLoginView.as_view(), name='admin_login'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('me/', CurrentUserView.as_view(), name='current_user'),
    path('change-password/', ChangePasswordView.as_view(), name='change_password'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('admin/users/count/', UserCountAPIView.as_view(), name='user_count'),
]
