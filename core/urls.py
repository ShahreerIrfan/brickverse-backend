from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from rest_framework.views import APIView
from rest_framework.response import Response
from apps.products.views import CategoryListView, CategoryDetailView, ProductSectionListView
from apps.marketing.views import (
    NewsletterSubscribeView,
    CouponListCreateView,
    CouponDetailView,
    CouponValidateView,
)

class APIRootView(APIView):
    def get(self, request):
        return Response({
            "name": "Kawaii Subete E-Commerce REST API",
            "version": "1.1.0",
            "endpoints": {
                "auth": "/api/auth/",
                "products": "/api/products/",
                "categories": "/api/categories/",
                "sections": "/api/sections/",
                "promotions": "/api/promotions/all/",
                "orders": "/api/orders/track/",
                "cart": "/api/orders/cart/",
                "wishlist": "/api/orders/wishlist/",
                "trust_perks": "/api/orders/trust-perks/",
                "marketing_nav": "/api/marketing/nav-links/",
                "marketing_store": "/api/marketing/store-info/",
                "newsletter": "/api/newsletter/subscribe/",
                "coupons": "/api/coupons/",
                "partner_stores": "/api/stores/",
                "logs": "/api/logs/",
                "blog": "/api/blog/posts/",
                "expenses": "/api/expenses/",
            }
        })

def secure_media_serve(request, path, document_root=None, show_indexes=False):
    response = serve(request, path, document_root=document_root, show_indexes=show_indexes)
    response['X-Content-Type-Options'] = 'nosniff'
    response['Content-Security-Policy'] = "default-src 'none'; style-src 'unsafe-inline'; sandbox"
    response['Cache-Control'] = 'public, max-age=31536000, immutable'
    return response


# F-04: Throttled Django admin login to eliminate unthrottled brute-force / credential-stuffing
from django.core.cache import cache
from django.http import HttpResponse

_original_admin_login = admin.site.login

def rate_limited_admin_login(request, extra_context=None):
    ip = request.META.get('HTTP_CF_CONNECTING_IP') or request.META.get('REMOTE_ADDR', 'unknown')
    cache_key = f"django_admin_login_throttle_{ip}"
    failed_attempts = cache.get(cache_key, 0)
    
    if failed_attempts >= 5:
        resp = HttpResponse(
            "Too Many Requests: Admin login temporarily locked due to consecutive failed attempts. Please retry in 15 minutes.",
            status=429,
            content_type="text/plain"
        )
        resp['Retry-After'] = '900'
        return resp

    response = _original_admin_login(request, extra_context=extra_context)

    if request.method == 'POST':
        if response.status_code == 200:
            cache.set(cache_key, failed_attempts + 1, timeout=900)
        elif response.status_code in (302, 303):
            cache.delete(cache_key)

    return response

admin.site.login = rate_limited_admin_login


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', APIRootView.as_view(), name='api-root'),
    
    # Modular Apps
    path('api/auth/', include('apps.users.urls')),
    path('api/products/', include('apps.products.urls')),
    path('api/promotions/', include('apps.promotions.urls')),
    path('api/orders/', include('apps.orders.urls')),
    path('api/marketing/', include('apps.marketing.urls')),
    path('api/stores/', include('apps.stores.urls')),
    path('api/logs/', include('apps.logs.urls')),
    path('api/blog/', include('apps.blog.urls')),
    path('api/expenses/', include('apps.expense.urls')),

    # Direct top-level aliases
    path('api/categories/', CategoryListView.as_view(), name='top-categories'),
    path('api/categories/<str:id>/', CategoryDetailView.as_view(), name='top-category-detail'),
    path('api/sections/', ProductSectionListView.as_view(), name='top-sections'),
    path('api/newsletter/subscribe/', NewsletterSubscribeView.as_view(), name='top-newsletter'),
    path('api/coupons/', CouponListCreateView.as_view(), name='top-coupons-list-create'),
    path('api/coupons/<int:pk>/', CouponDetailView.as_view(), name='top-coupons-detail'),
    path('api/coupons/validate/', CouponValidateView.as_view(), name='top-coupons-validate'),

    # Media files serving with XSS sandboxing (Production & Development)
    re_path(r'^media/(?P<path>.*)$', secure_media_serve, {'document_root': settings.MEDIA_ROOT}),
    re_path(r'^api/media/(?P<path>.*)$', secure_media_serve, {'document_root': settings.MEDIA_ROOT}),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

