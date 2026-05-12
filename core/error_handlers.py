"""
Custom error handlers for both HTML and JSON responses.
"""
from django.http import JsonResponse
from django.shortcuts import render


def custom_404_view(request, exception=None):
    """
    Custom 404 error handler.
    Returns JSON for API requests, HTML for browser requests.
    """
    # Check if this is an API request (Content-Type or Accept header)
    if request.path.startswith('/api/') or 'application/json' in request.META.get('HTTP_ACCEPT', ''):
        return JsonResponse({
            'error': 'Not Found',
            'message': 'The requested resource was not found.',
            'status': 404,
            'path': request.path
        }, status=404)
    
    # Return HTML template for browser requests
    return render(request, '404.html', status=404)


def custom_500_view(request):
    """
    Custom 500 error handler.
    Returns JSON for API requests, HTML for browser requests.
    """
    if request.path.startswith('/api/') or 'application/json' in request.META.get('HTTP_ACCEPT', ''):
        return JsonResponse({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred. Please try again later.',
            'status': 500
        }, status=500)
    
    return render(request, '500.html', status=500)


def custom_403_view(request, exception=None):
    """
    Custom 403 error handler.
    Returns JSON for API requests, HTML for browser requests.
    """
    if request.path.startswith('/api/') or 'application/json' in request.META.get('HTTP_ACCEPT', ''):
        return JsonResponse({
            'error': 'Forbidden',
            'message': 'You do not have permission to access this resource.',
            'status': 403
        }, status=403)
    
    return render(request, '403.html', status=403)


def custom_400_view(request, exception=None):
    """
    Custom 400 error handler.
    Returns JSON for API requests, HTML for browser requests.
    """
    if request.path.startswith('/api/') or 'application/json' in request.META.get('HTTP_ACCEPT', ''):
        return JsonResponse({
            'error': 'Bad Request',
            'message': 'The request could not be understood or was missing required parameters.',
            'status': 400
        }, status=400)
    
    return render(request, '404.html', status=400)  # Use 404 template for 400 errors in browser
