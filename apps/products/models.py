import os
import random
import uuid
from django.db import models
from django.utils.text import slugify


def _safe_upload_path(folder, filename):
    # Real photos (phone/WhatsApp/camera) routinely have filenames far longer
    # than FileField's 100-char limit, or with spaces/unicode/#, which SVG
    # assets never did. Store under a short sanitized name + random suffix.
    stem, ext = os.path.splitext(os.path.basename(filename))
    stem = slugify(stem)[:40] or "image"
    return f"{folder}/{stem}-{uuid.uuid4().hex[:8]}{ext.lower()}"


def product_image_upload_to(instance, filename):
    return _safe_upload_path("products", filename)


def product_gallery_upload_to(instance, filename):
    return _safe_upload_path("products/gallery", filename)


class Category(models.Model):
    """A single, self-referential category tree. A category with no parent
    is a top-level category (what the storefront's mega menu and category
    rail show); any category can itself have children, to any depth, via
    the parent field - this replaced the old fixed two-level
    Category/SubCategory split so the admin can nest categories as deep as
    they need (Parent > Subcategory > Sub-subcategory > ...)."""

    id = models.CharField(max_length=100, primary_key=True)
    parent = models.ForeignKey(
        'self', null=True, blank=True, related_name='children', on_delete=models.SET_NULL
    )
    label = models.CharField(max_length=150)
    slug = models.CharField(max_length=150, blank=True)
    color = models.CharField(max_length=20, default="#FF4D6D")
    icon_type = models.CharField(max_length=50, blank=True, help_text="e.g. figure, toon, brick, code")
    category_icon = models.CharField(max_length=500, blank=True, default="", help_text="Category icon name, SVG path, or image URL")
    category_icon_file = models.FileField(upload_to='categories/icons/', blank=True, null=True)
    featured = models.BooleanField(default=False)
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    show_in_mega_menu = models.BooleanField(default=True, help_text="Show this category in the homepage hero mega menu")
    mega_menu_order = models.IntegerField(default=0, help_text="Display order within the homepage mega menu")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'label']
        verbose_name_plural = 'Categories'

    def save(self, *args, **kwargs):
        if not self.slug and self.label:
            self.slug = slugify(self.label)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.parent.label} > {self.label}" if self.parent_id else self.label


class ProductSection(models.Model):
    id = models.CharField(max_length=100, primary_key=True)
    eyebrow = models.CharField(max_length=100)
    eyebrow_color = models.CharField(max_length=20, default="#FF4D6D")
    title = models.CharField(max_length=150)
    item_count = models.CharField(max_length=50, default="0 items")
    accent = models.CharField(max_length=20, default="#FF4D6D")
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order', 'title']

    def __str__(self):
        return self.title


class Product(models.Model):
    id = models.CharField(max_length=150, primary_key=True)
    slug = models.SlugField(max_length=200, blank=True)
    sku = models.CharField(max_length=100, blank=True, null=True)
    section = models.ForeignKey(ProductSection, related_name='products', on_delete=models.SET_NULL, null=True, blank=True)
    category = models.CharField(max_length=100)
    category_color = models.CharField(max_length=20, default="#FF4D6D")
    subcategory = models.ForeignKey(Category, related_name='products', on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    image = models.FileField(upload_to=product_image_upload_to, max_length=255, blank=True, null=True)
    image_file = models.FileField(upload_to=product_image_upload_to, max_length=255, blank=True, null=True)
    card_bg = models.CharField(max_length=20, default="#FFEAF0")
    rating = models.FloatField(default=5.0)
    reviews = models.IntegerField(default=0)
    
    # Pricing & Stock (4 key fields + discount percentage)
    regular_price = models.CharField(max_length=50, blank=True, default="৳0.00")
    discounted_price = models.CharField(max_length=50, blank=True, default="৳0.00")
    trade_price = models.CharField(max_length=50, blank=True, default="৳0.00")
    discount_percent = models.IntegerField(default=0, blank=True)
    stock = models.IntegerField(default=100)
    
    # Backward compatibility helpers
    price = models.CharField(max_length=50, blank=True, default="৳0.00")
    original_price = models.CharField(max_length=50, blank=True, null=True)
    accent = models.CharField(max_length=20, default="#FF4D6D")
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at', '-id']

    def save(self, *args, **kwargs):
        if not self.slug and self.name:
            self.slug = slugify(self.name)
        if not self.id:
            self.id = self.slug or f"prod-{random.randint(1000, 9999)}"
        if not self.sku:
            clean_part = slugify(self.name).upper()[:6].replace('-', '') or "PROD"
            self.sku = f"KS-{clean_part}-{random.randint(1000, 9999)}"
            
        # Synchronize regular_price & original_price
        if self.regular_price and self.regular_price != "৳0.00":
            self.original_price = self.regular_price
        elif self.original_price and not self.regular_price:
            self.regular_price = self.original_price
            
        # Synchronize discounted_price & price
        if self.discounted_price and self.discounted_price != "৳0.00":
            self.price = self.discounted_price
        elif self.price and not self.discounted_price:
            self.discounted_price = self.price
            
        # Calculate discount percentage if not manually set
        try:
            reg_clean = float(str(self.regular_price).replace('৳', '').replace(',', '').strip())
            disc_clean = float(str(self.discounted_price).replace('৳', '').replace(',', '').strip())
            if reg_clean > disc_clean > 0:
                self.discount_percent = round(((reg_clean - disc_clean) / reg_clean) * 100)
        except (ValueError, TypeError, ZeroDivisionError):
            pass

        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class ProductGalleryImage(models.Model):
    product = models.ForeignKey(Product, related_name='gallery_images', on_delete=models.CASCADE)
    image_file = models.FileField(upload_to=product_gallery_upload_to, max_length=255, blank=True, null=True)
    image_url = models.CharField(max_length=500, blank=True)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'id']
        verbose_name_plural = 'Product Gallery Images'

    def __str__(self):
        return f"Gallery image for {self.product.name}"


class ProductReview(models.Model):
    product = models.ForeignKey(Product, related_name='reviews_list', on_delete=models.CASCADE)
    author_name = models.CharField(max_length=100)
    rating = models.IntegerField(default=5)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.author_name} on {self.product.name} ({self.rating}★)"

