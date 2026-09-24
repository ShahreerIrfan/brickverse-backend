from rest_framework import generics, filters, status
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q, F, Case, When, Value, FloatField, RestrictedError
from django.db.models.functions import Cast, Coalesce, NullIf, Replace
from .models import category_subtree_ids, Category, ProductSection, Product, ProductReview, ProductGalleryImage
from .serializers import (
    CategorySerializer,
    ProductSectionSerializer,
    ProductSerializer,
    ProductReviewSerializer,
    ProductGalleryImageSerializer,
)

class CategoryListView(generics.ListCreateAPIView):
    """Public: top-level categories only (what the storefront's mega menu
    and category rail show), each with its direct children nested one
    level deep as `subcategories`."""
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    queryset = Category.objects.filter(parent__isnull=True).prefetch_related('children').order_by('order', 'label')
    serializer_class = CategorySerializer
    pagination_class = None


class CategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    lookup_field = 'id'

    def perform_destroy(self, instance):
        # Children keep existing (parent becomes null, via on_delete=SET_NULL)
        # rather than being silently deleted along with their parent.
        instance.delete()


class CategoryTreeListView(generics.ListAPIView):
    """Admin: every category at every depth, flat, for building the full
    tree (indentation + parent picker) client-side via each row's `parent`."""
    queryset = Category.objects.all().order_by('order', 'label')
    serializer_class = CategorySerializer
    pagination_class = None


class MegaMenuReorderView(APIView):
    """Set which categories show in the homepage hero mega menu and their order.

    Accepts {"ids": ["cat-1", "cat-2", ...]} - the full ordered list of
    category ids that should appear in the mega menu. Any category not in
    the list is turned off; categories in the list get show_in_mega_menu=True
    and mega_menu_order set to their position.
    """

    def post(self, request):
        ids = request.data.get('ids', [])
        if not isinstance(ids, list):
            return Response({"error": "ids must be a list of category ids"}, status=status.HTTP_400_BAD_REQUEST)

        valid_ids = list(
            Category.objects.filter(id__in=ids).values_list('id', flat=True)
        )
        ordered_ids = [cid for cid in ids if cid in valid_ids]

        Category.objects.exclude(id__in=ordered_ids).update(show_in_mega_menu=False)
        for index, cat_id in enumerate(ordered_ids):
            Category.objects.filter(id=cat_id).update(show_in_mega_menu=True, mega_menu_order=index)

        return Response({"success": True, "count": len(ordered_ids)})


class HomepageSectionsReorderView(APIView):
    """Set which top-level categories appear as homepage sections and their order.

    Accepts {"ids": ["cat-1", "cat-2", ...]} - the full ordered list of
    top-level category ids to show. Anything not in the list is turned off;
    listed categories get show_on_homepage=True and homepage_order set to
    their position. Only top-level categories are accepted.
    """

    def post(self, request):
        ids = request.data.get('ids', [])
        if not isinstance(ids, list):
            return Response({"error": "ids must be a list of category ids"}, status=status.HTTP_400_BAD_REQUEST)

        valid_ids = set(Category.objects.filter(id__in=ids, parent__isnull=True).values_list('id', flat=True))
        ordered_ids = [cid for cid in ids if cid in valid_ids]

        Category.objects.exclude(id__in=ordered_ids).update(show_on_homepage=False)
        for index, cat_id in enumerate(ordered_ids):
            Category.objects.filter(id=cat_id).update(show_on_homepage=True, homepage_order=index)

        return Response({"success": True, "count": len(ordered_ids)})


class HomepageSectionListView(APIView):
    """Storefront: the admin-selected top-level categories, in order, each
    with its newest products (including products filed under any of its
    subcategories). Categories with no active products are left out so the
    homepage never shows an empty row."""

    def get(self, request):
        try:
            limit = max(1, min(int(request.query_params.get('limit', 8)), 24))
        except ValueError:
            limit = 8

        sections = []
        categories = Category.objects.filter(
            parent__isnull=True, is_active=True, show_on_homepage=True
        ).order_by('homepage_order', 'label')
        for cat in categories:
            subtree = category_subtree_ids(cat.id)
            qs = (
                Product.objects.filter(Q(category__iexact=cat.id) | Q(subcategory_id__in=subtree), is_active=True)
                .select_related('subcategory')
                .order_by('-created_at', '-id')
            )
            total = qs.count()
            if total == 0:
                continue
            sections.append({
                "id": cat.id,
                "label": cat.label,
                "slug": cat.slug,
                "color": cat.color,
                "icon_type": cat.icon_type,
                "categoryIcon": cat.category_icon,
                "productCount": total,
                "products": ProductSerializer(qs[:limit], many=True, context={'request': request}).data,
            })
        return Response(sections)


class ProductSectionListView(generics.ListAPIView):
    queryset = ProductSection.objects.filter(is_active=True).prefetch_related('products__subcategory').order_by('order')
    serializer_class = ProductSectionSerializer
    pagination_class = None


_category_subtree_ids = category_subtree_ids


class ProductListView(generics.ListCreateAPIView):
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    serializer_class = ProductSerializer
    pagination_class = None

    def get_queryset(self):
        queryset = Product.objects.all().select_related('subcategory__parent').prefetch_related('group_items__child').order_by('-created_at', '-id')
        category = self.request.query_params.get('category')
        subcategory = self.request.query_params.get('subcategory')
        section = self.request.query_params.get('section')
        search = self.request.query_params.get('search')
        badge = self.request.query_params.get('badge')

        is_active_param = self.request.query_params.get('is_active')
        show_all = (
            self.request.query_params.get('all') in ('true', 'True', '1') or
            self.request.query_params.get('admin') in ('true', 'True', '1') or
            is_active_param == 'all'
        )

        if is_active_param in ('true', 'True', '1'):
            queryset = queryset.filter(is_active=True)
        elif is_active_param in ('false', 'False', '0'):
            queryset = queryset.filter(is_active=False)
        elif not show_all:
            # Default for storefront: only active products are visible across the website
            queryset = queryset.filter(is_active=True)

        if category:
            match = Category.objects.filter(Q(id=category) | Q(slug=category) | Q(label__iexact=category)).first()
            if match:
                subtree_ids = _category_subtree_ids(match.id)
                queryset = queryset.filter(Q(category__iexact=match.id) | Q(subcategory_id__in=subtree_ids))
            else:
                queryset = queryset.filter(Q(category__icontains=category) | Q(id__icontains=category))
        if subcategory:
            match = Category.objects.filter(Q(id=subcategory) | Q(slug=subcategory) | Q(label__iexact=subcategory)).first()
            if match:
                subtree_ids = _category_subtree_ids(match.id)
                queryset = queryset.filter(subcategory_id__in=subtree_ids)
            else:
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
        return self._apply_shop_filters(queryset)

    # Prices are stored as text like "৳1,200.00"; this reads them as numbers so
    # the shop can filter and sort in the database.
    @staticmethod
    def _price_number(field):
        expr = F(field)
        for junk in ('৳', ',', '$', ' '):
            expr = Replace(expr, Value(junk), Value(''))
        return Coalesce(Cast(NullIf(expr, Value('')), FloatField()), Value(0.0))

    def _apply_shop_filters(self, queryset):
        params = self.request.query_params

        def number(name):
            try:
                return float(params.get(name))
            except (TypeError, ValueError):
                return None

        min_price, max_price, min_rating = number('min_price'), number('max_price'), number('min_rating')
        on_sale = params.get('on_sale') in ('1', 'true', 'True')
        sort = params.get('sort') or 'newest'

        needs_price = (
            min_price is not None or max_price is not None or on_sale or sort in ('price_asc', 'price_desc')
        )
        if needs_price:
            # An empty discounted price means "sold at the regular price".
            queryset = queryset.annotate(
                sell_num=Case(
                    When(discounted_price='', then=self._price_number('price')),
                    default=self._price_number('discounted_price'),
                    output_field=FloatField(),
                ),
                regular_num=Case(
                    When(regular_price='', then=self._price_number('original_price')),
                    default=self._price_number('regular_price'),
                    output_field=FloatField(),
                ),
            )
        if min_price is not None:
            queryset = queryset.filter(sell_num__gte=min_price)
        if max_price is not None:
            queryset = queryset.filter(sell_num__lte=max_price)
        if on_sale:
            queryset = queryset.filter(regular_num__gt=F('sell_num'))
        if min_rating is not None:
            queryset = queryset.filter(rating__gte=min_rating)

        ordering = {
            'price_asc': ('sell_num', '-created_at', '-id'),
            'price_desc': ('-sell_num', '-created_at', '-id'),
            'rating': ('-rating', '-created_at', '-id'),
            'name_asc': ('name', '-id'),
            'discount': ('-discount_percent', '-created_at', '-id'),
        }.get(sort)
        if ordering:
            queryset = queryset.order_by(*ordering)
        return queryset

    def list(self, request, *args, **kwargs):
        # Plain array (existing behaviour) unless the caller asks for a page.
        if 'page' not in request.query_params:
            return super().list(request, *args, **kwargs)
        queryset = self.filter_queryset(self.get_queryset())
        try:
            page = max(1, int(request.query_params.get('page', 1)))
            size = min(60, max(1, int(request.query_params.get('page_size', 20))))
        except ValueError:
            page, size = 1, 20
        total = queryset.count()
        start = (page - 1) * size
        rows = list(queryset[start:start + size])
        data = self.get_serializer(rows, many=True).data
        return Response({
            'count': total,
            'page': page,
            'pageSize': size,
            'hasMore': start + size < total,
            'results': data,
        })


def _in_bundle_message(ids):
    from .models import GroupedProductItem
    rows = GroupedProductItem.objects.filter(child_id__in=ids).exclude(group_id__in=ids).select_related('child', 'group')
    parts = sorted({f'"{r.child.name}" (in bundle "{r.group.name}")' for r in rows})
    return "Can't delete a product that is part of a grouped product: " + ", ".join(parts) + ". Remove it from the bundle first."


class ProductDetailView(generics.RetrieveUpdateDestroyAPIView):
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    queryset = Product.objects.all().select_related('subcategory__parent')
    serializer_class = ProductSerializer

    def get_object(self):
        lookup = self.kwargs.get('id')
        allow_inactive = (
            self.request.query_params.get('all') in ('true', 'True', '1') or
            self.request.query_params.get('admin') in ('true', 'True', '1') or
            self.request.method in ('PUT', 'PATCH', 'DELETE')
        )
        qs = Product.objects.select_related('subcategory__parent').prefetch_related('group_items__child')
        if not allow_inactive:
            qs = qs.filter(is_active=True)
        obj = qs.filter(
            Q(id=lookup) | Q(slug=lookup) | Q(sku=lookup)
        ).first()
        if not obj:
            from django.http import Http404
            raise Http404("Product not found")
        return obj

    def destroy(self, request, *args, **kwargs):
        try:
            return super().destroy(request, *args, **kwargs)
        except RestrictedError:
            return Response({"error": _in_bundle_message([self.get_object().id])}, status=status.HTTP_400_BAD_REQUEST)


class ProductReviewCreateView(generics.CreateAPIView):
    queryset = ProductReview.objects.all()
    serializer_class = ProductReviewSerializer

    def perform_create(self, serializer):
        product_id = self.kwargs.get('product_id')
        product = Product.objects.get(id=product_id)
        serializer.save(product=product)


class ProductBulkDeleteView(generics.GenericAPIView):
    parser_classes = [JSONParser, FormParser, MultiPartParser]

    def post(self, request, *args, **kwargs):
        ids = request.data.get('ids', [])
        if not ids or not isinstance(ids, list):
            return Response({"error": "A list of product IDs is required in 'ids'."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            deleted_count, _ = Product.objects.filter(id__in=ids).delete()
        except RestrictedError:
            return Response({"error": _in_bundle_message(ids)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({
            "success": True,
            "deleted_count": deleted_count,
            "message": f"Successfully deleted {deleted_count} product(s)."
        }, status=status.HTTP_200_OK)

    def delete(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)


class ProductGalleryImageDeleteView(generics.DestroyAPIView):
    queryset = ProductGalleryImage.objects.all()
    serializer_class = ProductGalleryImageSerializer
    lookup_field = 'id'
