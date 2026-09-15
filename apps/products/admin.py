from django.contrib import admin
from .models import Category, ProductSection, Product, ProductReview


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'label', 'parent', 'color', 'icon_type', 'featured', 'order', 'is_active', 'show_in_mega_menu', 'mega_menu_order')
    list_editable = ('featured', 'order', 'is_active', 'show_in_mega_menu', 'mega_menu_order')
    list_filter = ('parent', 'is_active')
    search_fields = ('label', 'id', 'slug')


@admin.register(ProductSection)
class ProductSectionAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'eyebrow', 'item_count', 'order', 'is_active')
    list_editable = ('order', 'is_active')
    search_fields = ('title', 'eyebrow')


class ProductReviewInline(admin.TabularInline):
    model = ProductReview
    extra = 0


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'id', 'sku', 'category', 'regular_price', 'discounted_price', 'trade_price', 'discount_percent', 'stock', 'is_active')
    list_filter = ('section', 'category', 'subcategory', 'is_active')
    search_fields = ('name', 'sku', 'id', 'slug')
    list_editable = ('stock', 'is_active')
    inlines = [ProductReviewInline]


@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'author_name', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('author_name', 'comment', 'product__name')
