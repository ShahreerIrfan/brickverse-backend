from django.contrib import admin
from .models import TrustPerk, Cart, CartItem, WishlistItem, Order, OrderItem
from apps.products.models import restock_product, deduct_stock

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
    readonly_fields = ('product', 'product_name', 'price', 'quantity', 'bundle_items', 'is_preorder')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'customer_name', 'customer_phone', 'customer_email', 'total_amount', 'status', 'carrier', 'created_at')
    list_filter = ('status', 'carrier', 'created_at')
    search_fields = ('order_number', 'customer_name', 'customer_email', 'customer_phone', 'tracking_number')
    inlines = [OrderItemInline]
    readonly_fields = ('order_number', 'created_at')
    actions = ['mark_as_cancelled', 'mark_as_processing', 'mark_as_shipped', 'mark_as_delivered']

    def get_actions(self, request):
        actions = super().get_actions(request)
        # Disable dangerous hard 'delete_selected' bulk action so orders cannot be mass-erased by accident
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

    @admin.action(description="❌ Mark selected orders as CANCELLED (Restocks Inventory)")
    def mark_as_cancelled(self, request, queryset):
        count = 0
        for order in queryset:
            if order.status != 'cancelled':
                for item in order.items.all():
                    if not item.is_preorder and item.product:
                        restock_product(item.product, item.quantity, bundle_items=item.bundle_items)
                order.status = 'cancelled'
                order.save(update_fields=['status'])
                count += 1
        self.message_user(request, f"Successfully cancelled {count} order(s) and restocked inventory.")

    @admin.action(description="⏳ Mark selected orders as PROCESSING")
    def mark_as_processing(self, request, queryset):
        count = queryset.update(status='processing')
        self.message_user(request, f"Marked {count} order(s) as Processing.")

    @admin.action(description="🚚 Mark selected orders as SHIPPED")
    def mark_as_shipped(self, request, queryset):
        count = queryset.update(status='shipped')
        self.message_user(request, f"Marked {count} order(s) as Shipped.")

    @admin.action(description="✅ Mark selected orders as DELIVERED")
    def mark_as_delivered(self, request, queryset):
        count = queryset.update(status='delivered')
        self.message_user(request, f"Marked {count} order(s) as Delivered.")

    def delete_model(self, request, obj):
        # Restock product before deleting a single order
        if obj.status != 'cancelled':
            for item in obj.items.all():
                if not item.is_preorder and item.product:
                    restock_product(item.product, item.quantity, bundle_items=item.bundle_items)
        super().delete_model(request, obj)
