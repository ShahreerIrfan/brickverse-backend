from django.urls import path
from .views import (
    TrustPerkListView,
    CartView,
    WishlistView,
    OrderTrackView,
    MyOrdersView,
    OrderListView,
    OrderDetailUpdateView,
    AdminDashboardStatsView,
)

urlpatterns = [
    path('', OrderListView.as_view(), name='order-root'),
    path('trust-perks/', TrustPerkListView.as_view(), name='trust-perks'),
    path('cart/', CartView.as_view(), name='cart'),
    path('wishlist/', WishlistView.as_view(), name='wishlist'),
    path('mine/', MyOrdersView.as_view(), name='order-mine'),
    path('track/', OrderTrackView.as_view(), name='order-track'),
    path('list/', OrderListView.as_view(), name='order-list'),
    path('admin-stats/', AdminDashboardStatsView.as_view(), name='admin-stats'),
    path('<str:id>/', OrderDetailUpdateView.as_view(), name='order-detail-update'),
]

