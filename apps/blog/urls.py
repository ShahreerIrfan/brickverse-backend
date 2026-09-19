from django.urls import path
from .views import (
    BlogPostListView,
    BlogPostDetailView,
    BlogCategoryListView,
    BlogTagListView,
    AdminBlogPostListView,
    AdminBlogPostDetailView,
    AdminCategoryListView,
    AdminCategoryDetailView,
    AdminTagListView,
    AdminTagDetailView,
    BlogMediaUploadView,
)

urlpatterns = [
    path('posts/', BlogPostListView.as_view(), name='blog-post-list'),
    path('posts/<slug:slug>/', BlogPostDetailView.as_view(), name='blog-post-detail'),
    path('categories/', BlogCategoryListView.as_view(), name='blog-category-list'),
    path('tags/', BlogTagListView.as_view(), name='blog-tag-list'),

    path('admin/posts/', AdminBlogPostListView.as_view(), name='blog-admin-post-list'),
    path('admin/posts/<int:id>/', AdminBlogPostDetailView.as_view(), name='blog-admin-post-detail'),
    path('admin/categories/', AdminCategoryListView.as_view(), name='blog-admin-category-list'),
    path('admin/categories/<int:id>/', AdminCategoryDetailView.as_view(), name='blog-admin-category-detail'),
    path('admin/tags/', AdminTagListView.as_view(), name='blog-admin-tag-list'),
    path('admin/tags/<int:id>/', AdminTagDetailView.as_view(), name='blog-admin-tag-detail'),

    path('media/upload/', BlogMediaUploadView.as_view(), name='blog-media-upload'),
]
