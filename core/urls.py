from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from rest_framework.views import APIView
from rest_framework.response import Response
from apps.products.views import CategoryListView, SubCategoryListView, ProductSectionListView
from apps.marketing.views import NewsletterSubscribeView

class APIRootView(APIView):
    def get(self, request):
        return Response({
            "name": "Brickverse E-Commerce REST API",
            "version": "1.1.0",
            "endpoints": {
                "auth": "/api/auth/",
                "products": "/api/products/",
                "categories": "/api/categories/",
                "subcategories": "/api/subcategories/",
                "sections": "/api/sections/",
                "promotions": "/api/promotions/all/",
                "orders": "/api/orders/track/",
                "cart": "/api/orders/cart/",
                "wishlist": "/api/orders/wishlist/",
                "trust_perks": "/api/orders/trust-perks/",
                "marketing_nav": "/api/marketing/nav-links/",
                "marketing_store": "/api/marketing/store-info/",
                "newsletter": "/api/newsletter/subscribe/",
            }
        })

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', APIRootView.as_view(), name='api-root'),
    
    # Modular Apps
    path('api/auth/', include('apps.users.urls')),
    path('api/products/', include('apps.products.urls')),
    path('api/promotions/', include('apps.promotions.urls')),
    path('api/orders/', include('apps.orders.urls')),
    path('api/marketing/', include('apps.marketing.urls')),

    # Direct top-level aliases
    path('api/categories/', CategoryListView.as_view(), name='top-categories'),
    path('api/subcategories/', SubCategoryListView.as_view(), name='top-subcategories'),
    path('api/sections/', ProductSectionListView.as_view(), name='top-sections'),
    path('api/newsletter/subscribe/', NewsletterSubscribeView.as_view(), name='top-newsletter'),

    # Media files serving (Production & Development)
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
