from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import AuthCodeViewSet, CodeLoginAPIView, CodeMeAPIView

app_name = 'authcodes'

# Admin router
router = DefaultRouter()
router.register(r'', AuthCodeViewSet, basename='authcode')

urlpatterns = [
    # Public endpoints
    path('public/code-login/', CodeLoginAPIView.as_view(), name='code_login'),
    path('public/code-me/', CodeMeAPIView.as_view(), name='code_me'),
    
    # Admin endpoints (with IsSuperAdmin permission)
    path('admin/auth-codes/', include(router.urls)),
]
