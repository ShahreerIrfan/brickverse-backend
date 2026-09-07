from rest_framework import generics, filters, status
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from django.db.models import Q
from .models import Category, SubCategory, ProductSection, Product, ProductReview
from .serializers import (
    CategorySerializer,
    SubCategorySerializer,
    ProductSectionSerializer,
    ProductSerializer,
    ProductReviewSerializer,
)

class CategoryListView(generics.ListCreateAPIView):
    queryset = Category.objects.prefetch_related('subcategories').all().order_by('order', 'label')
    serializer_class = CategorySerializer
    pagination_class = None


class CategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    lookup_field = 'id'


class SubCategoryListView(generics.ListCreateAPIView):
    serializer_class = SubCategorySerializer
    pagination_class = None

    def get_queryset(self):
        queryset = SubCategory.objects.all().order_by('order', 'label')
        category_id = self.request.query_params.get('category')
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        return queryset


class SubCategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = SubCategory.objects.all()
    serializer_class = SubCategorySerializer
    lookup_field = 'id'


class ProductSectionListView(generics.ListAPIView):
    queryset = ProductSection.objects.filter(is_active=True).prefetch_related('products__subcategory').order_by('order')
    serializer_class = ProductSectionSerializer
    pagination_class = None


class ProductListView(generics.ListCreateAPIView):
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    serializer_class = ProductSerializer
    pagination_class = None

    def get_queryset(self):
        queryset = Product.objects.all().select_related('subcategory').order_by('order')
        category = self.request.query_params.get('category')
        subcategory = self.request.query_params.get('subcategory')
        section = self.request.query_params.get('section')
        search = self.request.query_params.get('search')
        badge = self.request.query_params.get('badge')

        if category:
            queryset = queryset.filter(Q(category__icontains=category) | Q(id__icontains=category))
        if subcategory:
            queryset = queryset.filter(Q(subcategory_id=subcategory) | Q(subcategory__slug=subcategory) | Q(subcategory__label__icontains=subcategory))
        if section:
            queryset = queryset.filter(section_id=section)
        if badge:
            queryset = queryset.filter(badge__iexact=badge)
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(sku__icontains=search) |
                Q(category__icontains=search) |
                Q(description__icontains=search)
            )
        return queryset


class ProductDetailView(generics.RetrieveUpdateDestroyAPIView):
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    queryset = Product.objects.all().select_related('subcategory')
    serializer_class = ProductSerializer

    def get_object(self):
        lookup = self.kwargs.get('id')
        try:
            return Product.objects.select_related('subcategory').get(
                Q(id=lookup) | Q(slug=lookup) | Q(sku=lookup)
            )
        except Product.DoesNotExist:
            from django.http import Http404
            raise Http404("Product not found")


class ProductReviewCreateView(generics.CreateAPIView):
    queryset = ProductReview.objects.all()
    serializer_class = ProductReviewSerializer

    def perform_create(self, serializer):
        product_id = self.kwargs.get('product_id')
        product = Product.objects.get(id=product_id)
        serializer.save(product=product)

