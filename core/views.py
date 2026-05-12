from django.shortcuts import render
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from .permissions import CodeScopePermission


def _recent_activity_list(limit_per_source=8, total_limit=25):
    """
    Build a unified recent activity list from gallery, news, videos, opendata, auth code usages.
    Returns list of dicts with: id, activity_type, action, timestamp, item_id, title.
    """
    from django.utils import timezone

    activities = []

    # GalleryItem – "Image uploaded"
    try:
        from gallery.models import GalleryItem
        for obj in GalleryItem.objects.order_by('-created_at')[:limit_per_source]:
            activities.append({
                'id': f'gallery-{obj.id}',
                'activity_type': 'gallery',
                'action': 'Image uploaded',
                'timestamp': timezone.make_aware(obj.created_at) if timezone.is_naive(obj.created_at) else obj.created_at,
                'item_id': obj.id,
                'title': (obj.caption_en or obj.caption_ar or '')[:80] or None,
            })
    except Exception:
        pass

    # NewsItem – "Article published"
    try:
        from news.models import NewsItem
        for obj in NewsItem.objects.order_by('-created_at')[:limit_per_source]:
            activities.append({
                'id': f'news-{obj.id}',
                'activity_type': 'news',
                'action': 'Article published',
                'timestamp': timezone.make_aware(obj.created_at) if timezone.is_naive(obj.created_at) else obj.created_at,
                'item_id': obj.id,
                'title': (obj.title_en or obj.title_ar or '')[:80] or None,
            })
    except Exception:
        pass

    # VideoGalleryItem – "Video added" / "Video processed"
    try:
        from videogallery.models import VideoGalleryItem
        for obj in VideoGalleryItem.objects.order_by('-created_at')[:limit_per_source]:
            activities.append({
                'id': f'video-{obj.id}',
                'activity_type': 'video',
                'action': 'Video processed' if obj.status == 'ready' else 'Video added',
                'timestamp': timezone.make_aware(obj.created_at) if timezone.is_naive(obj.created_at) else obj.created_at,
                'item_id': obj.id,
                'title': (obj.caption_en or obj.caption_ar or '')[:80] or None,
            })
    except Exception:
        pass

    # OpenDataItem – "Dataset updated"
    try:
        from opendata.models import OpenDataItem
        for obj in OpenDataItem.objects.order_by('-created_at')[:limit_per_source]:
            activities.append({
                'id': f'opendata-{obj.id}',
                'activity_type': 'opendata',
                'action': 'Dataset updated',
                'timestamp': timezone.make_aware(obj.created_at) if timezone.is_naive(obj.created_at) else obj.created_at,
                'item_id': obj.id,
                'title': (obj.caption_en or obj.caption_ar or '')[:80] or None,
            })
    except Exception:
        pass

    # AuthCodeUsage – "Auth code used"
    try:
        from authcodes.models import AuthCodeUsage
        for obj in AuthCodeUsage.objects.select_related('auth_code').order_by('-used_at')[:limit_per_source]:
            activities.append({
                'id': f'authcode-{obj.id}',
                'activity_type': 'auth_code',
                'action': 'Auth code used',
                'timestamp': timezone.make_aware(obj.used_at) if timezone.is_naive(obj.used_at) else obj.used_at,
                'item_id': obj.auth_code_id,
                'title': None,
            })
    except Exception:
        pass

    # Sort by timestamp descending and cap
    activities.sort(key=lambda x: x['timestamp'], reverse=True)
    out = activities[:total_limit]

    # Serialize timestamps to ISO
    for a in out:
        a['timestamp'] = a['timestamp'].isoformat()
    return out


def home_view(request):
    """
    Homepage view showing API information.
    """
    return render(request, 'index.html')


class ReportDetailAPIView(APIView):
    """
    Example protected API that requires VIEW_REPORT scope.
    GET /api/reports/{id}/
    
    This endpoint demonstrates CodeScopePermission usage.
    Access requires either:
    1. Super admin JWT token, OR
    2. Code-based JWT token with scope='VIEW_REPORT' and matching resource_id
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [CodeScopePermission]
    required_scope = 'VIEW_REPORT'

    def get(self, request, id):
        """
        Retrieve a report by ID.
        """
        # In a real application, you would fetch the report from database
        # For demonstration, we return mock data
        
        report_data = {
            'id': id,
            'title': f'Report #{id}',
            'content': 'This is a protected report that requires VIEW_REPORT scope.',
            'created_at': '2026-01-18T12:00:00Z',
            'status': 'published',
        }

        return Response(report_data, status=status.HTTP_200_OK)


class RecentActivityAPIView(APIView):
    """
    GET /api/dashboard/recent-activity/
    Returns a paginated list of recent activities (gallery, news, videos, opendata, auth code usages).
    Query params: page (default 1), page_size (default 10, max 50).
    Requires authenticated staff/super_admin.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            page = max(1, int(request.query_params.get('page', 1)))
        except (TypeError, ValueError):
            page = 1
        try:
            page_size = min(50, max(1, int(request.query_params.get('page_size', 10))))
        except (TypeError, ValueError):
            page_size = 10

        all_activities = _recent_activity_list(total_limit=500)
        count = len(all_activities)
        total_pages = (count + page_size - 1) // page_size if count > 0 else 1
        start = (page - 1) * page_size
        end = start + page_size
        results = all_activities[start:end]

        return Response({
            'results': results,
            'count': count,
            'page': page,
            'page_size': page_size,
            'total_pages': total_pages,
        })
