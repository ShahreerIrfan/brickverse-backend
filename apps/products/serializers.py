from rest_framework import serializers
from .models import Category, SubCategory, ProductSection, Product, ProductReview, ProductGalleryImage

class SubCategorySerializer(serializers.ModelSerializer):
    categoryId = serializers.CharField(source='category_id', required=False)

    class Meta:
        model = SubCategory
        fields = ['id', 'categoryId', 'category', 'label', 'slug', 'description', 'image', 'order', 'is_active']
        extra_kwargs = {
            'category': {'required': False},
        }

    def create(self, validated_data):
        category_id = validated_data.pop('category_id', None) or (validated_data.get('category').id if validated_data.get('category') else None)
        if category_id and not validated_data.get('category'):
            validated_data['category'] = Category.objects.get(id=category_id)
        return super().create(validated_data)


class CategorySerializer(serializers.ModelSerializer):
    subcategories = SubCategorySerializer(many=True, read_only=True)
    productCount = serializers.SerializerMethodField(read_only=True)
    categoryIcon = serializers.CharField(source='category_icon', required=False, allow_blank=True)

    class Meta:
        model = Category
        fields = [
            'id',
            'label',
            'color',
            'icon_type',
            'category_icon',
            'categoryIcon',
            'category_icon_file',
            'featured',
            'order',
            'subcategories',
            'productCount',
        ]
        extra_kwargs = {
            'category_icon': {'required': False, 'allow_blank': True},
            'category_icon_file': {'required': False, 'allow_null': True},
        }

    def get_productCount(self, obj):
        from .models import Product
        return Product.objects.filter(category__icontains=obj.id).count()

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
    categoryColor = serializers.CharField(source='category_color', required=False, allow_blank=True)
    cardBg = serializers.CharField(source='card_bg', required=False, allow_blank=True)
    originalPrice = serializers.CharField(source='original_price', required=False, allow_null=True, allow_blank=True)
    regularPrice = serializers.CharField(source='regular_price', required=False, allow_blank=True)
    discountedPrice = serializers.CharField(source='discounted_price', required=False, allow_blank=True)
    tradePrice = serializers.CharField(source='trade_price', required=False, allow_blank=True)
    discountPercent = serializers.IntegerField(source='discount_percent', required=False)
    subcategory = SubCategorySerializer(read_only=True)
    subcategoryId = serializers.CharField(write_only=True, required=False, allow_null=True, allow_blank=True)
    reviews_list = ProductReviewSerializer(many=True, read_only=True)
    gallery_images = ProductGalleryImageSerializer(many=True, read_only=True)
    sectionId = serializers.CharField(source='section_id', required=False, allow_null=True, allow_blank=True)

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
            'is_active',
            'order',
            'gallery_images',
            'reviews_list',
        ]
        extra_kwargs = {
            'section': {'required': False},
            'slug': {'required': False},
            'sku': {'required': False},
            'image': {'required': False, 'allow_blank': True},
            'image_file': {'required': False, 'allow_null': True},
        }

    def create(self, validated_data):
        subcat_id = validated_data.pop('subcategoryId', None)
        if subcat_id:
            try:
                validated_data['subcategory'] = SubCategory.objects.get(id=subcat_id)
            except SubCategory.DoesNotExist:
                pass
        
        if not validated_data.get('section') and not validated_data.get('section_id'):
            first_sec = ProductSection.objects.first()
            if first_sec:
                validated_data['section'] = first_sec

        image_file = validated_data.get('image_file')
        if image_file:
            instance = super().create(validated_data)
            if instance.image_file:
                instance.image = instance.image_file.url
                instance.save(update_fields=['image'])
        else:
            if not validated_data.get('image'):
                validated_data['image'] = '/images/figure-samurai-red.svg'
            instance = super().create(validated_data)

        # Process multi-file gallery images from request.FILES
        request = self.context.get('request')
        if request and hasattr(request, 'FILES'):
            gallery_files = request.FILES.getlist('gallery_files')
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

    def update(self, instance, validated_data):
        subcat_id = validated_data.pop('subcategoryId', None)
        if subcat_id is not None:
            if subcat_id == "":
                instance.subcategory = None
            else:
                try:
                    instance.subcategory = SubCategory.objects.get(id=subcat_id)
                except SubCategory.DoesNotExist:
                    pass

        instance = super().update(instance, validated_data)
        if instance.image_file:
            instance.image = instance.image_file.url
            instance.save(update_fields=['image'])

        # Process multi-file gallery images from request.FILES
        request = self.context.get('request')
        if request and hasattr(request, 'FILES'):
            gallery_files = request.FILES.getlist('gallery_files')
            if gallery_files:
                for idx, g_file in enumerate(gallery_files):
                    g_obj = ProductGalleryImage.objects.create(
                        product=instance,
                        image_file=g_file,
                        order=instance.gallery_images.count() + idx
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

