from django.contrib import admin
from .models import TrustPerk, Cart, CartItem, WishlistItem, Order, OrderItem

@admin.register(TrustPerk)
class TrustPerkAdmin(admin.ModelAdmin):
    list_display = ('title', 'subtitle', 'icon_type', 'color', 'order', 'is_active')
    list_editable = ('order', 'is_active')


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('session_id', 'created_at', 'updated_at')
    inlines = [CartItemInline]


@admin.register(WishlistItem)
class WishlistItemAdmin(admin.ModelAdmin):
    list_display = ('session_id', 'product', 'created_at')


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'customer_name', 'customer_email', 'total_amount', 'status', 'created_at')
    list_filter = ('status', 'carrier')
    search_fields = ('order_number', 'customer_name', 'customer_email', 'tracking_number')
    inlines = [OrderItemInline]
