from rest_framework import serializers
from .models import TrustPerk, Cart, CartItem, WishlistItem, Order, OrderItem
from apps.products.serializers import ProductSerializer

class TrustPerkSerializer(serializers.ModelSerializer):
    iconType = serializers.CharField(source='icon_type')

    class Meta:
        model = TrustPerk
        fields = ['id', 'title', 'subtitle', 'iconType', 'color', 'order']


class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    productId = serializers.CharField(write_only=True)

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'productId', 'quantity', 'created_at']

    def create(self, validated_data):
        product_id = validated_data.pop('productId')
        cart = validated_data['cart']
        item, created = CartItem.objects.get_or_create(
            cart=cart,
            product_id=product_id,
            defaults={'quantity': validated_data.get('quantity', 1)}
        )
        if not created:
            item.quantity += validated_data.get('quantity', 1)
            item.save()
        return item


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    itemCount = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ['id', 'session_id', 'items', 'itemCount', 'created_at']

    def get_itemCount(self, obj):
        return sum(item.quantity for item in obj.items.all())


class WishlistItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    productId = serializers.CharField(write_only=True)

    class Meta:
        model = WishlistItem
        fields = ['id', 'session_id', 'product', 'productId', 'created_at']


class OrderItemSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    sku = serializers.SerializerMethodField()
    slug = serializers.SerializerMethodField()
    productId = serializers.SerializerMethodField()
    bundleItems = serializers.JSONField(source='bundle_items', read_only=True)
    isPreorder = serializers.BooleanField(source='is_preorder', read_only=True)
    is_preorder = serializers.BooleanField(read_only=True)
    originalPrice = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = [
            'id',
            'product',
            'productId',
            'product_name',
            'price',
            'quantity',
            'image',
            'sku',
            'slug',
            'bundleItems',
            'isPreorder',
            'is_preorder',
            'originalPrice',
        ]

    def _get_product_instance(self, obj):
        prod = obj.product
        if not prod and getattr(obj, 'product_id', None):
            try:
                from apps.products.models import Product
                prod = Product.objects.filter(id=obj.product_id).first()
            except Exception:
                pass
        if not prod and getattr(obj, 'product_name', None):
            try:
                from apps.products.models import Product
                prod = Product.objects.filter(name=obj.product_name).first()
            except Exception:
                pass
        return prod

    def get_productId(self, obj):
        if obj.product_id:
            return str(obj.product_id)
        prod = self._get_product_instance(obj)
        return str(prod.id) if prod else ""

    def get_slug(self, obj):
        prod = self._get_product_instance(obj)
        if prod and getattr(prod, 'slug', None):
            return prod.slug
        return str(obj.product_id) if obj.product_id else ""

    def get_originalPrice(self, obj):
        prod = self._get_product_instance(obj)
        if prod:
            for field in ['regular_price', 'original_price']:
                val_str = getattr(prod, field, None)
                if val_str:
                    try:
                        import re
                        num = float(re.sub(r'[^\d.]', '', str(val_str)))
                        if num > float(obj.price):
                            return num
                    except Exception:
                        pass
        return None

    def get_image(self, obj):
        prod = self._get_product_instance(obj)
        if prod:
            img = prod.image or getattr(prod, 'image_file', None)
            if img:
                try:
                    return img.url
                except Exception:
                    return str(img)
            try:
                first_gal = prod.gallery_images.first()
                if first_gal:
                    if first_gal.image_file:
                        try:
                            return first_gal.image_file.url
                        except Exception:
                            return str(first_gal.image_file)
                    if first_gal.image_url:
                        return first_gal.image_url
            except Exception:
                pass
        return "/images/figure-samurai-red.svg"

    def get_sku(self, obj):
        prod = self._get_product_instance(obj)
        if prod and getattr(prod, 'sku', None):
            return prod.sku
        return ""


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    shipping_cost = serializers.SerializerMethodField()
    discount = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            'id',
            'order_number',
            'customer_name',
            'customer_email',
            'customer_phone',
            'shipping_address',
            'total_amount',
            'shipping_cost',
            'discount',
            'status',
            'tracking_number',
            'carrier',
            'created_at',
            'items',
        ]

    def get_shipping_cost(self, obj):
        cost = getattr(obj, 'shipping_cost', None)
        if cost is not None:
            return float(cost)
        try:
            items_total = sum(float(item.price) * item.quantity for item in obj.items.all())
            total = float(obj.total_amount)
            if total > items_total:
                return round(total - items_total, 2)
        except Exception:
            pass
        addr = (obj.shipping_address or "").lower()
        return 60.0 if "dhaka" in addr else 120.0

    def get_discount(self, obj):
        try:
            items_total = sum(float(item.price) * item.quantity for item in obj.items.all())
            ship_cost = self.get_shipping_cost(obj)
            total = float(obj.total_amount)
            diff = (items_total + ship_cost) - total
            if diff > 0.01:
                return round(diff, 2)
        except Exception:
            pass
        return 0.0
