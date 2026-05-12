from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path
from django.views.generic import RedirectView
from book.views import (
    PublicPublicationDetailAPIView,
    PublicPublicationListAPIView,
    PublicPublicationStatsAPIView,
    PublicPublicationSummaryAPIView,
    PublicationAskAPIView,
    PublicationChatHistoryAPIView,
)

# Customize Django Admin
admin.site.site_header = "Arabian Gulf Security 4 Portal"
admin.site.site_title = "Arabian Gulf Security 4 Portal"
admin.site.index_title = "Welcome to Administration"

urlpatterns = [
    # Homepage - redirect to admin login
    path('', RedirectView.as_view(url='/admin/login/', permanent=False), name='home'),
    
    # Django admin
    path('admin/', admin.site.urls),
    path('summernote/', include('django_summernote.urls')),
    
    # Authentication endpoints
    path('api/auth/', include('accounts.urls')),
    
    # Auth codes endpoints (public + admin)
    path('api/', include('authcodes.urls')),
    
    # Protected API endpoints
    path('api/', include('core.urls')),

    # Category endpoints
    path('api/', include('category.urls')),
    
    # Book endpoints
    path('api/book/', include('book.urls')),

    # Public landing publications endpoints
    path('api/publications/', PublicPublicationListAPIView.as_view(), name='public-publication-list'),
    path('api/publications/stats/', PublicPublicationStatsAPIView.as_view(), name='public-publication-stats'),
    path('api/publications/<int:pk>/', PublicPublicationDetailAPIView.as_view(), name='public-publication-detail'),
    path('api/publications/<int:pk>/summary/', PublicPublicationSummaryAPIView.as_view(), name='public-publication-summary'),
    path('api/publications/<int:pk>/ask/', PublicationAskAPIView.as_view(), name='public-publication-ask'),
    path('api/publications/<int:pk>/chat-history/', PublicationChatHistoryAPIView.as_view(), name='public-publication-chat-history'),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Custom error handlers
handler404 = 'core.error_handlers.custom_404_view'
handler500 = 'core.error_handlers.custom_500_view'
handler403 = 'core.error_handlers.custom_403_view'
handler400 = 'core.error_handlers.custom_400_view'
