from django.urls import path

from .views import ReportDetailAPIView, RecentActivityAPIView

app_name = 'core'

urlpatterns = [
    # Example protected endpoint
    path('reports/<str:id>/', ReportDetailAPIView.as_view(), name='report_detail'),
    # Dashboard
    path('dashboard/recent-activity/', RecentActivityAPIView.as_view(), name='recent_activity'),
]
