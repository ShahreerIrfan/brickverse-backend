import re
from django.db import transaction
from django.db.models import Q
from rest_framework import serializers
from .image_utils import normalize_image_upload
from .models import Category, ProductSection, Product, ProductReview, ProductGalleryImage, GroupedProductItem, category_subtree_ids


class CategoryChildSerializer(serializers.ModelSerializer):
    """One level of a category's direct children - used both for the
    storefront's `subcategories` list and for a product's `subcategory`.
    Kept intentionally slim (no further nesting) to match how the
    storefront has always consumed this."""

    class Meta:
        model = Category
        fields = ['id', 'label', 'slug', 'order', 'is_active']


class CategorySerializer(serializers.ModelSerializer):
    subcategories = CategoryChildSerializer(source='children', many=True, read_only=True)
    childrenCount = serializers.SerializerMethodField(read_only=True)
    productCount = serializers.SerializerMethodField(read_only=True)
    subtreeProductCount = serializers.SerializerMethodField(read_only=True)
    categoryIcon = serializers.CharField(source='category_icon', required=False, allow_blank=True)
    parentLabel = serializers.CharField(source='parent.label', read_only=True, default=None)

    class Meta:
        model = Category
        fields = [
            'id',
            'label',
            'slug',
            'parent',
            'parentLabel',
            'color',
            'icon_type',
            'category_icon',
            'categoryIcon',
            'category_icon_file',
            'featured',
            'order',
            'is_active',
            'show_in_mega_menu',
            'mega_menu_order',
            'show_on_homepage',
            'homepage_order',
            'subcategories',
            'childrenCount',
            'productCount',
            'subtreeProductCount',
        ]
        extra_kwargs = {
            'category_icon': {'required': False, 'allow_blank': True},
            'category_icon_file': {'required': False, 'allow_null': True},
            'parent': {'required': False, 'allow_null': True},
        }

    def get_childrenCount(self, obj):
        return obj.children.count()

    def get_productCount(self, obj):
        from .models import Product
        return Product.objects.filter(category__icontains=obj.id).count()

    def get_subtreeProductCount(self, obj):
        from .models import Product
        ids = category_subtree_ids(obj.id)
        return Product.objects.filter(Q(category__iexact=obj.id) | Q(subcategory_id__in=ids)).count()

    def validate_parent(self, value):
        if value and self.instance and value.id == self.instance.id:
            raise serializers.ValidationError("A category can't be its own parent.")
        if value and self.instance:
            node = value
            while node is not None:
                if node.id == self.instance.id:
                    raise serializers.ValidationError("A category can't be nested under one of its own children.")
                node = node.parent
        return value

    def create(self, validated_data):
        icon_file = validated_data.get('category_icon_file')
        instance = super().create(validated_data)
        if icon_file and instance.category_icon_file:
            instance.category_icon = instance.category_icon_file.url
            instance.save(update_fields=['category_icon'])
        return instance

    def update(self, instance, validated_data):
        icon_file = validated_data.get('category_icon_file')
        instance = super().update(instance, validated_data)
        if icon_file and instance.category_icon_file:
            instance.category_icon = instance.category_icon_file.url
            instance.save(update_fields=['category_icon'])
        return instance


class ProductGalleryImageSerializer(serializers.ModelSerializer):
    imageUrl = serializers.SerializerMethodField()

    class Meta:
        model = ProductGalleryImage
        fields = ['id', 'image_file', 'image_url', 'imageUrl', 'order']

    def get_imageUrl(self, obj):
        if obj.image_file:
            return obj.image_file.url
        return obj.image_url or ''


class ProductReviewSerializer(serializers.ModelSerializer):
    author = serializers.CharField(source='author_name')
    date = serializers.DateTimeField(source='created_at', format='%Y-%m-%d', read_only=True)

    class Meta:
        model = ProductReview
        fields = ['id', 'author', 'rating', 'comment', 'date']


class ProductSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    categoryColor = serializers.CharField(source='category_color', required=False, allow_blank=True)
    cardBg = serializers.CharField(source='card_bg', required=False, allow_blank=True)
    originalPrice = serializers.CharField(source='original_price', required=False, allow_null=True, allow_blank=True)
    regularPrice = serializers.CharField(source='regular_price', required=False, allow_blank=True)
    discountedPrice = serializers.CharField(source='discounted_price', required=False, allow_blank=True)
    tradePrice = serializers.CharField(source='trade_price', required=False, allow_blank=True)
    discountPercent = serializers.IntegerField(source='discount_percent', required=False)
    subcategory = CategoryChildSerializer(read_only=True)
    subcategoryId = serializers.CharField(write_only=True, required=False, allow_null=True, allow_blank=True)
    reviews_list = ProductReviewSerializer(many=True, read_only=True)
    gallery_images = ProductGalleryImageSerializer(many=True, read_only=True)
    sectionId = serializers.CharField(source='section_id', required=False, allow_null=True, allow_blank=True)
    productType = serializers.ChoiceField(source='product_type', choices=Product.PRODUCT_TYPE_CHOICES, required=False)
    # Write side of a grouped product's contents: [{"childId": "x", "quantity": 2}, ...].
    # Read side (groupItems + bundleTotal) is added in to_representation.
    groupItems = serializers.JSONField(write_only=True, required=False)
    categoryPath = serializers.SerializerMethodField(read_only=True)

    def get_categoryPath(self, obj):
        """Ancestor chain for the breadcrumb: [top-level category, ..., immediate
        subcategory]. Falls back to the flat `category` field for older products
        that only have that set."""
        chain, node, seen = [], obj.subcategory, set()
        while node and node.id not in seen:
            seen.add(node.id)
            chain.append(node)
            node = node.parent
        chain.reverse()
        if chain:
            return [{'id': c.id, 'label': c.label, 'slug': c.slug or c.id} for c in chain]
        if obj.category:
            match = Category.objects.filter(
                Q(id=obj.category) | Q(slug=obj.category) | Q(label__iexact=obj.category)
            ).first()
            if match:
                return [{'id': match.id, 'label': match.label, 'slug': match.slug or match.id}]
            return [{'id': obj.category, 'label': obj.category, 'slug': obj.category}]
        return []

    class Meta:
        model = Product
        fields = [
            'id',
            'slug',
            'sku',
            'section',
            'sectionId',
            'category',
            'categoryColor',
            'subcategory',
            'subcategoryId',
            'categoryPath',
            'name',
            'description',
            'image',
            'image_file',
            'cardBg',
            'rating',
            'reviews',
            'regularPrice',
            'discountedPrice',
            'tradePrice',
            'discountPercent',
            'price',
            'originalPrice',
            'accent',
            'stock',
            'productType',
            'groupItems',
            'is_active',
            'order',
            'gallery_images',
            'reviews_list',
        ]
        extra_kwargs = {
            'section': {'required': False},
            'slug': {'required': False},
            'sku': {'required': False},
            'image_file': {'required': False, 'allow_null': True},
        }

    @staticmethod
    def _price_value(text):
        cleaned = re.sub(r'[^0-9.]', '', text or '')
        try:
            return float(cleaned) if cleaned else 0.0
        except ValueError:
            return 0.0

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.is_grouped:
            lines, total = [], 0.0
            for item in instance.group_items.all():
                child = item.child
                unit = child.discounted_price or child.price or ''
                value = self._price_value(unit)
                total += value * item.quantity
                lines.append({
                    'childId': child.id,
                    'name': child.name,
                    'slug': child.slug,
                    'image': self.get_image(child),
                    'quantity': item.quantity,
                    'price': unit,
                    'priceValue': value,
                    'stock': child.stock,
                })
            data['groupItems'] = lines
            data['bundleTotal'] = round(total, 2)
            data['stock'] = instance.available_stock
        else:
            data['groupItems'] = []
            data['bundleTotal'] = None
        return data

    def validate_groupItems(self, value):
        if value in (None, ''):
            return []
        if not isinstance(value, list):
            raise serializers.ValidationError('Bundle contents must be a list.')
        if len(value) > 50:
            raise serializers.ValidationError('A bundle can contain at most 50 products.')
        rows, seen = [], set()
        for raw in value:
            if not isinstance(raw, dict):
                raise serializers.ValidationError('Each bundle line must be an object.')
            child_id = str(raw.get('childId') or raw.get('child_id') or '').strip()
            try:
                qty = int(raw.get('quantity', 1))
            except (TypeError, ValueError):
                raise serializers.ValidationError(f'Quantity for "{child_id}" must be a whole number.')
            if not child_id:
                raise serializers.ValidationError('Every bundle line needs a product.')
            if qty < 1:
                raise serializers.ValidationError('Bundle quantities must be at least 1.')
            if child_id in seen:
                raise serializers.ValidationError('The same product is listed twice - change its quantity instead.')
            seen.add(child_id)
            rows.append((child_id, qty))

        children = {p.id: p for p in Product.objects.filter(id__in=[r[0] for r in rows])}
        existing = {}
        if self.instance is not None:
            existing = {g.child_id: g.quantity for g in self.instance.group_items.all()}
        result = []
        for child_id, qty in rows:
            child = children.get(child_id)
            if child is None:
                raise serializers.ValidationError(f'Product "{child_id}" does not exist.')
            if self.instance is not None and child.id == self.instance.id:
                raise serializers.ValidationError('A bundle cannot contain itself.')
            if child.is_grouped:
                raise serializers.ValidationError(
                    f'"{child.name}" is a grouped product itself - only simple products can be added to a bundle.'
                )
            if qty > child.stock and qty > existing.get(child.id, 0):
                raise serializers.ValidationError(
                    f'"{child.name}" has only {child.stock} in stock, so a bundle cannot include {qty}.'
                )
            result.append({'child': child, 'quantity': qty})
        return result

    def validate(self, attrs):
        attrs = super().validate(attrs)
        instance = self.instance
        final_type = attrs.get('product_type') or (instance.product_type if instance else Product.TYPE_SIMPLE)
        items = attrs.get('groupItems')

        if final_type == Product.TYPE_GROUPED:
            already_has_items = bool(instance and instance.group_items.exists())
            if items is None and not already_has_items:
                raise serializers.ValidationError({'groupItems': 'Add at least one product to the bundle.'})
            if items is not None and len(items) == 0:
                raise serializers.ValidationError({'groupItems': 'Add at least one product to the bundle.'})
            if instance is not None and not instance.is_grouped:
                used_in = list(instance.used_in_groups.select_related('group').values_list('group__name', flat=True))
                if used_in:
                    raise serializers.ValidationError({
                        'productType': f'"{instance.name}" is already part of the bundle(s) {", ".join(used_in)}. '
                                       'Remove it from those first.'
                    })
        return attrs

    @staticmethod
    def _sync_group_items(instance, items):
        instance.group_items.all().delete()
        GroupedProductItem.objects.bulk_create([
            GroupedProductItem(group=instance, child=row['child'], quantity=row['quantity'], order=index)
            for index, row in enumerate(items)
        ])

    def get_image(self, obj):
        img = obj.image or getattr(obj, 'image_file', None)
        if img:
            try:
                url = img.url if hasattr(img, 'url') else str(img)
            except Exception:
                url = str(img)
            if url:
                if url.startswith(('http://', 'https://', '/images/')):
                    return url
                if not url.startswith('/media/'):
                    clean = url.lstrip('/')
                    if not clean.startswith('media/'):
                        url = f"/media/{clean}"
                    else:
                        url = f"/{clean}"
                request = self.context.get('request')
                if request:
                    return request.build_absolute_uri(url)
                return url
        return "/images/figure-samurai-red.svg"

    @staticmethod
    def _share_image_path(instance):
        if instance.image and instance.image_file.name != instance.image.name:
            Product.objects.filter(pk=instance.pk).update(image_file=instance.image.name)
            instance.image_file.name = instance.image.name

    @transaction.atomic
    def create(self, validated_data):
        group_items = validated_data.pop('groupItems', None)
        subcat_id = validated_data.pop('subcategoryId', None)
        if subcat_id:
            try:
                validated_data['subcategory'] = Category.objects.get(id=subcat_id)
            except Category.DoesNotExist:
                pass
        
        if not validated_data.get('section') and not validated_data.get('section_id'):
            first_sec = ProductSection.objects.first()
            if first_sec:
                validated_data['section'] = first_sec

        request = self.context.get('request')
        img_upload = None
        if request and hasattr(request, 'FILES'):
            img_upload = normalize_image_upload(request.FILES.get('image') or request.FILES.get('image_file'))

        if img_upload:
            # Save the upload once (to `image`) and share that stored path with
            # `image_file` afterwards. Handing the same large upload to both
            # FileFields made the second save fail on Linux: Django *moves* a
            # spooled temp file into place, so the source was already gone.
            validated_data['image'] = img_upload
            validated_data.pop('image_file', None)

        instance = super().create(validated_data)
        if img_upload:
            self._share_image_path(instance)
        if instance.is_grouped and group_items:
            self._sync_group_items(instance, group_items)

        # Process multi-file gallery images from request.FILES (Maximum 4 allowed)
        if request and hasattr(request, 'FILES'):
            gallery_files = [normalize_image_upload(f) for f in request.FILES.getlist('gallery_files')[:4]]
            for idx, g_file in enumerate(gallery_files):
                g_obj = ProductGalleryImage.objects.create(
                    product=instance,
                    image_file=g_file,
                    order=idx
                )
                if g_obj.image_file:
                    g_obj.image_url = g_obj.image_file.url
                    g_obj.save(update_fields=['image_url'])

        return instance

    @transaction.atomic
    def update(self, instance, validated_data):
        group_items = validated_data.pop('groupItems', None)
        subcat_id = validated_data.pop('subcategoryId', None)
        if subcat_id is not None:
            if subcat_id == "":
                instance.subcategory = None
            else:
                try:
                    instance.subcategory = Category.objects.get(id=subcat_id)
                except Category.DoesNotExist:
                    pass

        request = self.context.get('request')
        if request and hasattr(request, 'FILES'):
            img_upload = normalize_image_upload(request.FILES.get('image') or request.FILES.get('image_file'))
            if img_upload:
                validated_data['image'] = img_upload
                validated_data.pop('image_file', None)

        instance = super().update(instance, validated_data)
        if request and hasattr(request, 'FILES') and (request.FILES.get('image') or request.FILES.get('image_file')):
            self._share_image_path(instance)
        if instance.is_grouped:
            if group_items is not None:
                self._sync_group_items(instance, group_items)
        else:
            instance.group_items.all().delete()

        # Process deletion of existing gallery images if requested
        if request:
            delete_ids = []
            if hasattr(request, 'data') and hasattr(request.data, 'getlist'):
                delete_ids.extend(request.data.getlist('delete_gallery_ids'))
            if hasattr(request, 'data') and 'delete_gallery_ids' in request.data:
                val = request.data.get('delete_gallery_ids')
                if isinstance(val, list):
                    delete_ids.extend(val)
                elif isinstance(val, str) and ',' in val:
                    delete_ids.extend(val.split(','))
                elif isinstance(val, (int, str)):
                    delete_ids.append(val)
            if hasattr(request, 'POST') and hasattr(request.POST, 'getlist'):
                delete_ids.extend(request.POST.getlist('delete_gallery_ids'))

            clean_ids = []
            for item in delete_ids:
                item_str = str(item).strip()
                if item_str.isdigit():
                    clean_ids.append(int(item_str))

            if clean_ids:
                instance.gallery_images.filter(id__in=clean_ids).delete()

        # Process multi-file gallery images from request.FILES (Total maximum 4 gallery images)
        if request and hasattr(request, 'FILES'):
            current_count = instance.gallery_images.count()
            allowed_slots = max(0, 4 - current_count)
            gallery_files = [normalize_image_upload(f) for f in request.FILES.getlist('gallery_files')[:allowed_slots]]
            if gallery_files:
                for idx, g_file in enumerate(gallery_files):
                    g_obj = ProductGalleryImage.objects.create(
                        product=instance,
                        image_file=g_file,
                        order=current_count + idx
                    )
                    if g_obj.image_file:
                        g_obj.image_url = g_obj.image_file.url
                        g_obj.save(update_fields=['image_url'])

        return instance



class ProductSectionSerializer(serializers.ModelSerializer):
    eyebrowColor = serializers.CharField(source='eyebrow_color', read_only=True)
    itemCount = serializers.CharField(source='item_count', read_only=True)
    products = ProductSerializer(many=True, read_only=True)

    class Meta:
        model = ProductSection
        fields = [
            'id',
            'eyebrow',
            'eyebrowColor',
            'title',
            'itemCount',
            'accent',
            'order',
            'products',
        ]

