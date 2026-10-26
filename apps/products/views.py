from rest_framework import generics, filters, status
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models.functions import Cast, Coalesce, NullIf, Replace, MD5, Concat
from django.db.models import Q, F, Case, When, Value, FloatField, CharField, RestrictedError
from apps.users.permissions import IsAdminRole, IsAdminOrReadOnly

from .models import (
    category_subtree_ids, Category, ProductSection, Product,
    ProductReview, ProductGalleryImage, ProductLot, sync_product_from_active_lot
)
from .serializers import (
    CategorySerializer,
    ProductSectionSerializer,
    ProductSerializer,
    ProductReviewSerializer,
    ProductGalleryImageSerializer,
    ProductLotSerializer,
)


class CategoryListView(generics.ListCreateAPIView):
    """Public: top-level categories only (what the storefront's mega menu
    and category rail show), each with its direct children nested one
    level deep as `subcategories`."""
    permission_classes = [IsAdminOrReadOnly]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    queryset = Category.objects.filter(parent__isnull=True).prefetch_related('children').order_by('order', 'label')
    serializer_class = CategorySerializer
    pagination_class = None


class CategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAdminOrReadOnly]
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
    permission_classes = [IsAdminRole]
    queryset = Category.objects.all().order_by('order', 'label')
    serializer_class = CategorySerializer
    pagination_class = None


class MegaMenuReorderView(APIView):
    permission_classes = [IsAdminRole]
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
    permission_classes = [IsAdminRole]
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
            limit = max(1, min(int(request.query_params.get('limit', 10)), 50))
        except ValueError:
            limit = 10

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
    permission_classes = [IsAdminOrReadOnly]
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

        ids_param = self.request.query_params.get('ids')
        if ids_param:
            id_list = [x.strip() for x in ids_param.split(',') if x.strip()]
            queryset = queryset.filter(Q(id__in=id_list) | Q(slug__in=id_list))

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
        product_type = self.request.query_params.get('product_type') or self.request.query_params.get('type')
        deals = self.request.query_params.get('deals') in ('1', 'true', 'True')
        if deals or product_type == 'grouped':
            queryset = queryset.filter(product_type=Product.TYPE_GROUPED)
        elif product_type:
            queryset = queryset.filter(product_type=product_type)
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
            'newest': ('-created_at', '-id'),
        }.get(sort)

        seed = params.get('seed')
        is_random = sort in ('random', 'rand') or bool(seed)

        if ordering:
            queryset = queryset.order_by(*ordering)
        elif is_random:
            # Deterministic per-seed random sorting ensures clean pagination without duplicate items
            seed_val = str(seed).strip() if seed else 'kawaii_default_seed'
            queryset = queryset.annotate(
                _rand_order=MD5(Concat(Cast('id', CharField()), Value(seed_val)))
            ).order_by('_rand_order')

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
    permission_classes = [IsAdminOrReadOnly]
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
    permission_classes = [IsAdminRole]
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
    permission_classes = [IsAdminRole]
    queryset = ProductGalleryImage.objects.all()
    serializer_class = ProductGalleryImageSerializer
    lookup_field = 'id'


class ProductLotListCreateView(APIView):
    permission_classes = [IsAdminOrReadOnly]
    parser_classes = [MultiPartParser, FormParser, JSONParser]


    def _get_product(self, product_id):
        product_id = str(product_id).strip()
        prod = Product.objects.filter(id=product_id).first()
        if not prod:
            prod = Product.objects.filter(slug=product_id).first()
        return prod

    def get(self, request, product_id):
        prod = self._get_product(product_id)
        if not prod:
            return Response({'error': f'Product "{product_id}" not found.'}, status=status.HTTP_404_NOT_FOUND)

        lots = prod.lots.all().order_by('created_at', 'id')
        active_lot = prod.active_lot
        total_remaining = sum(max(0, lot.remaining_quantity) for lot in lots if lot.is_active)

        serializer = ProductLotSerializer(lots, many=True)
        return Response({
            'productId': prod.id,
            'productName': prod.name,
            'currentStock': prod.stock,
            'currentTradePrice': prod.trade_price,
            'currentRegularPrice': prod.regular_price,
            'currentPrice': prod.price,
            'totalLotRemaining': total_remaining,
            'activeLotId': active_lot.id if active_lot else None,
            'activeLotNumber': active_lot.lot_number if active_lot else None,
            'lots': serializer.data,
        })

    def post(self, request, product_id):
        from django.db import transaction
        prod = self._get_product(product_id)
        if not prod:
            return Response({'error': f'Product "{product_id}" not found.'}, status=status.HTTP_404_NOT_FOUND)

        action = request.data.get('action')

        # Quick action: Initialize initial lot from current product stock if no lots exist
        if action == 'init_from_stock':
            with transaction.atomic():
                if prod.lots.exists():
                    return Response({'error': 'Product already has lots.'}, status=status.HTTP_400_BAD_REQUEST)
                qty = max(0, int(prod.stock or 0))
                lot = ProductLot.objects.create(
                    product=prod,
                    lot_number=f"LOT-INIT-{prod.id[:10].upper()}",
                    trade_price=prod.trade_price or "৳0.00",
                    mrp=prod.regular_price or prod.price or "৳0.00",
                    discounted_price=prod.discounted_price or "৳0.00",
                    initial_quantity=qty,
                    remaining_quantity=qty,
                    is_active=True,
                    notes="Initialized from legacy product stock"
                )
                prod.sync_from_active_lot()
                return Response({
                    'message': 'Initial lot created from product stock.',
                    'lot': ProductLotSerializer(lot).data,
                    'product': ProductSerializer(prod).data,
                }, status=status.HTTP_201_CREATED)

        # Standard new lot creation (Restock)
        raw_qty = request.data.get('quantity') or request.data.get('initialQuantity') or request.data.get('initial_quantity')
        try:
            qty = int(raw_qty)
            if qty <= 0:
                return Response({'error': 'Quantity must be greater than 0.'}, status=status.HTTP_400_BAD_REQUEST)
        except (TypeError, ValueError):
            return Response({'error': 'Valid quantity is required.'}, status=status.HTTP_400_BAD_REQUEST)

        trade_price = request.data.get('tradePrice') or request.data.get('trade_price') or prod.trade_price or "৳0.00"
        mrp = request.data.get('mrp') or request.data.get('regularPrice') or prod.regular_price or prod.price or "৳0.00"
        discounted_price = request.data.get('discountedPrice') or request.data.get('discounted_price') or ""
        lot_number = str(request.data.get('lotNumber') or request.data.get('lot_number') or '').strip()
        notes = str(request.data.get('notes') or '').strip()

        with transaction.atomic():
            lot = ProductLot.objects.create(
                product=prod,
                lot_number=lot_number,
                trade_price=str(trade_price).strip(),
                mrp=str(mrp).strip(),
                discounted_price=str(discounted_price).strip(),
                initial_quantity=qty,
                remaining_quantity=qty,
                is_active=True,
                notes=notes,
            )
            prod.sync_from_active_lot()

        return Response({
            'message': f'Lot "{lot.lot_number}" created successfully!',
            'lot': ProductLotSerializer(lot).data,
            'product': ProductSerializer(prod).data,
        }, status=status.HTTP_201_CREATED)


class ProductLotDetailView(APIView):
    permission_classes = [IsAdminOrReadOnly]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_object(self, pk):
        from django.http import Http404
        lot = ProductLot.objects.filter(pk=pk).select_related('product').first()
        if not lot:
            raise Http404(f"Lot '{pk}' not found.")
        return lot

    def get(self, request, pk):
        lot = self.get_object(pk)
        return Response(ProductLotSerializer(lot).data)

    def patch(self, request, pk):
        from django.db import transaction
        lot = self.get_object(pk)
        data = request.data

        with transaction.atomic():
            if 'remainingQuantity' in data or 'remaining_quantity' in data:
                raw_rem = data.get('remainingQuantity') if 'remainingQuantity' in data else data.get('remaining_quantity')
                try:
                    lot.remaining_quantity = max(0, int(raw_rem))
                except (TypeError, ValueError):
                    pass
            if 'initialQuantity' in data or 'initial_quantity' in data:
                raw_init = data.get('initialQuantity') if 'initialQuantity' in data else data.get('initial_quantity')
                try:
                    lot.initial_quantity = max(0, int(raw_init))
                except (TypeError, ValueError):
                    pass
            if 'tradePrice' in data or 'trade_price' in data:
                lot.trade_price = str(data.get('tradePrice') or data.get('trade_price')).strip()
            if 'mrp' in data:
                lot.mrp = str(data.get('mrp')).strip()
            if 'discountedPrice' in data or 'discounted_price' in data:
                lot.discounted_price = str(data.get('discountedPrice') or data.get('discounted_price')).strip()
            if 'lotNumber' in data or 'lot_number' in data:
                new_num = str(data.get('lotNumber') or data.get('lot_number')).strip()
                if new_num:
                    lot.lot_number = new_num
            if 'isActive' in data or 'is_active' in data:
                val = data.get('isActive') if 'isActive' in data else data.get('is_active')
                lot.is_active = str(val).lower() in ('true', '1', 'yes')
            if 'notes' in data:
                lot.notes = str(data.get('notes') or '').strip()

            lot.save()
            lot.product.sync_from_active_lot()

        return Response({
            'message': 'Lot updated successfully.',
            'lot': ProductLotSerializer(lot).data,
            'product': ProductSerializer(lot.product).data,
        })

    def delete(self, request, pk):
        from django.db import transaction
        lot = self.get_object(pk)
        product = lot.product

        with transaction.atomic():
            # Check if this lot is referenced by any orders
            has_orders = lot.order_items.exists()
            if has_orders:
                lot.is_active = False
                lot.save(update_fields=['is_active', 'updated_at'])
                product.sync_from_active_lot()
                return Response({'message': f'Lot "{lot.lot_number}" has order history and was deactivated instead of permanently deleted.'})
            else:
                lot.delete()
                product.sync_from_active_lot()
                return Response({'message': 'Lot was deleted successfully.'}, status=status.HTTP_204_NO_CONTENT)

