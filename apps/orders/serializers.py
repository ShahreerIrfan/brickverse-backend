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
    class Meta:
        model = OrderItem
        fields = ['id', 'product_name', 'price', 'quantity']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

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
            'status',
            'tracking_number',
            'carrier',
            'created_at',
            'items',
        ]
