from django.urls import path
from .views import (
    CategoryListView,
    CategoryDetailView,
    SubCategoryListView,
    SubCategoryDetailView,
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
    path('categories/', CategoryListView.as_view(), name='category-list'),
    path('categories/<str:id>/', CategoryDetailView.as_view(), name='category-detail'),
    path('subcategories/', SubCategoryListView.as_view(), name='subcategory-list'),
    path('subcategories/<str:id>/', SubCategoryDetailView.as_view(), name='subcategory-detail'),
    path('sections/', ProductSectionListView.as_view(), name='section-list'),
    path('<str:id>/', ProductDetailView.as_view(), name='product-detail'),
    path('<str:product_id>/reviews/', ProductReviewCreateView.as_view(), name='product-review-create'),
]

