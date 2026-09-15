from rest_framework import generics, filters, status
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q
from .models import Category, ProductSection, Product, ProductReview, ProductGalleryImage
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


class ProductSectionListView(generics.ListAPIView):
    queryset = ProductSection.objects.filter(is_active=True).prefetch_related('products__subcategory').order_by('order')
    serializer_class = ProductSectionSerializer
    pagination_class = None


def _category_subtree_ids(root_id):
    """A category's own id plus every descendant's id, so filtering by a
    parent (e.g. "Mobile") also catches products filed under any of its
    children/grandchildren (e.g. "AMOLED Display Mobile")."""
    ids = {root_id}
    frontier = [root_id]
    while frontier:
        children = list(Category.objects.filter(parent_id__in=frontier).values_list('id', flat=True))
        new_ids = [c for c in children if c not in ids]
        if not new_ids:
            break
        ids.update(new_ids)
        frontier = new_ids
    return ids


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
        return queryset


class ProductDetailView(generics.RetrieveUpdateDestroyAPIView):
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    queryset = Product.objects.all().select_related('subcategory')
    serializer_class = ProductSerializer

    def get_object(self):
        lookup = self.kwargs.get('id')
        obj = Product.objects.select_related('subcategory').filter(
            Q(id=lookup) | Q(slug=lookup) | Q(sku=lookup)
        ).first()
        if not obj:
            from django.http import Http404
            raise Http404("Product not found")
        return obj


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
        
        deleted_count, _ = Product.objects.filter(id__in=ids).delete()
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


class SeedCatalogAPIView(generics.GenericAPIView):
    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        import os
        import shutil
        import json
        from django.conf import settings

        # 1. Sync assets to media/products
        media_products_dir = os.path.join(settings.MEDIA_ROOT, "products")
        os.makedirs(media_products_dir, exist_ok=True)
        
        assets_dir = os.path.join(settings.BASE_DIR, "catalog_seed_assets")
        if os.path.exists(assets_dir):
            for fname in os.listdir(assets_dir):
                if fname.endswith(".svg"):
                    src = os.path.join(assets_dir, fname)
                    dst = os.path.join(media_products_dir, fname)
                    shutil.copy2(src, dst)

        # 2. Delete all existing products first
        deleted_count, _ = Product.objects.all().delete()

        # 3. Load fixture
        fixture_path = os.path.join(settings.BASE_DIR, "products_data.json")
        if not os.path.exists(fixture_path):
            return Response({"error": "products_data.json not found on server"}, status=status.HTTP_404_NOT_FOUND)

        with open(fixture_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        prod_count = 0
        cat_count = 0
        section_count = 0

        for item in data:
            model = item.get("model")
            pk = item.get("pk")
            fields = dict(item.get("fields", {}))

            if model == "products.productsection":
                ProductSection.objects.update_or_create(id=pk, defaults=fields)
                section_count += 1
            elif model == "products.category":
                Category.objects.update_or_create(id=pk, defaults=fields)
                cat_count += 1
            elif model == "products.product":
                sec_id = fields.pop("section", None)
                sec_obj = None
                if sec_id:
                    sec_obj = ProductSection.objects.filter(id=sec_id).first()
                fields["section"] = sec_obj

                raw_img = fields.pop("image", "")
                img_filename = os.path.basename(raw_img) if raw_img else "figure-samurai-red.svg"
                fields["image"] = f"products/{img_filename}"
                fields["image_file"] = f"products/{img_filename}"

                Product.objects.update_or_create(id=pk, defaults=fields)
                prod_count += 1

        return Response({
            "success": True,
            "deleted_previous_count": deleted_count,
            "seeded_product_count": prod_count,
            "message": f"Successfully deleted old products and seeded {prod_count} new products with SVG images!"
        })


