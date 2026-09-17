from django.db.models import Q
from django.core.files.storage import default_storage
from django.http import Http404
from rest_framework import generics
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.views import APIView
from rest_framework.response import Response
from apps.users.permissions import IsAdminRole
from .models import Category, Tag, BlogPost
from .serializers import (
    CategorySerializer,
    TagSerializer,
    BlogPostListSerializer,
    BlogPostDetailSerializer,
)


class BlogPostListView(generics.ListAPIView):
    """Public: published posts only, filterable by category/tag slug and free-text search."""
    serializer_class = BlogPostListSerializer

    def get_queryset(self):
        queryset = BlogPost.objects.filter(status='published').select_related('category', 'author').prefetch_related('tags')
        category = self.request.query_params.get('category')
        tag = self.request.query_params.get('tag')
        search = self.request.query_params.get('search')

        if category:
            queryset = queryset.filter(Q(category__slug=category) | Q(category_id=category))
        if tag:
            queryset = queryset.filter(Q(tags__slug=tag) | Q(tags__id=tag))
        if search:
            queryset = queryset.filter(Q(title__icontains=search) | Q(excerpt__icontains=search))

        return queryset.distinct()


class BlogPostDetailView(generics.RetrieveAPIView):
    """Public: a single published post by slug. 404s for drafts or missing posts."""
    serializer_class = BlogPostDetailSerializer
    lookup_field = 'slug'

    def get_queryset(self):
        return BlogPost.objects.filter(status='published').select_related('category', 'author').prefetch_related('tags', 'blocks')

    def get_object(self):
        obj = self.get_queryset().filter(slug=self.kwargs['slug']).first()
        if not obj:
            raise Http404("Post not found")
        return obj


class BlogCategoryListView(generics.ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    pagination_class = None


class BlogTagListView(generics.ListAPIView):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class AdminBlogPostListView(generics.ListCreateAPIView):
    """Admin: full post list including drafts."""
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    permission_classes = [IsAdminRole]
    queryset = BlogPost.objects.all().select_related('category', 'author').prefetch_related('tags', 'blocks')

    def get_serializer_class(self):
        return BlogPostDetailSerializer if self.request.method == 'POST' else BlogPostListSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        status_filter = self.request.query_params.get('status')
        search = self.request.query_params.get('search')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if search:
            queryset = queryset.filter(Q(title__icontains=search) | Q(excerpt__icontains=search))
        return queryset

    def perform_create(self, serializer):
        author = self.request.user if self.request.user.is_authenticated else None
        serializer.save(author=author)


class AdminBlogPostDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Admin: full CRUD (including nested blocks) on a single post."""
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    permission_classes = [IsAdminRole]
    queryset = BlogPost.objects.all().select_related('category', 'author').prefetch_related('tags', 'blocks')
    serializer_class = BlogPostDetailSerializer
    lookup_field = 'id'


class AdminCategoryListView(generics.ListCreateAPIView):
    permission_classes = [IsAdminRole]
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    pagination_class = None


class AdminCategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAdminRole]
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    lookup_field = 'id'


class AdminTagListView(generics.ListCreateAPIView):
    permission_classes = [IsAdminRole]
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class AdminTagDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAdminRole]
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    lookup_field = 'id'


class BlogMediaUploadView(APIView):
    """POST a single `file` multipart field, saved under media/blog/<filename>.
    Used by the admin block editor to upload images for image/gallery blocks."""
    permission_classes = [IsAdminRole]
    parser_classes = [MultiPartParser]

    def post(self, request):
        upload = request.FILES.get('file')
        if not upload:
            return Response({"error": "A 'file' field is required."}, status=400)

        saved_path = default_storage.save('blog/' + upload.name, upload)
        url = default_storage.url(saved_path)
        if request:
            url = request.build_absolute_uri(url)
        return Response({"url": url})
