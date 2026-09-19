from django.urls import path
from .views import (
    CategoryListView,
    CategoryDetailView,
    CategoryTreeListView,
    MegaMenuReorderView,
    ProductSectionListView,
    ProductListView,
    ProductDetailView,
    ProductReviewCreateView,
    ProductBulkDeleteView,
    ProductGalleryImageDeleteView,
)

urlpatterns = [
    path('', ProductListView.as_view(), name='product-list'),
    path('bulk-delete/', ProductBulkDeleteView.as_view(), name='product-bulk-delete'),
    path('gallery/<int:id>/', ProductGalleryImageDeleteView.as_view(), name='product-gallery-delete'),
    path('categories/mega-menu/reorder/', MegaMenuReorderView.as_view(), name='category-mega-menu-reorder'),
    path('categories/all/', CategoryTreeListView.as_view(), name='category-tree'),
    path('categories/', CategoryListView.as_view(), name='category-list'),
    path('categories/<str:id>/', CategoryDetailView.as_view(), name='category-detail'),
    path('sections/', ProductSectionListView.as_view(), name='section-list'),
    path('<str:id>/', ProductDetailView.as_view(), name='product-detail'),
    path('<str:product_id>/reviews/', ProductReviewCreateView.as_view(), name='product-review-create'),
]

