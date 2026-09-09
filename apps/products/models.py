import random
from django.db import models
from django.utils.text import slugify


class Category(models.Model):
    id = models.CharField(max_length=50, primary_key=True)
    label = models.CharField(max_length=100)
    color = models.CharField(max_length=20, default="#FF4D6D")
    icon_type = models.CharField(max_length=50, blank=True, help_text="e.g. figure, toon, brick, code")
    category_icon = models.CharField(max_length=500, blank=True, default="", help_text="Category icon name, SVG path, or image URL")
    category_icon_file = models.ImageField(upload_to='categories/icons/', blank=True, null=True)
    featured = models.BooleanField(default=False)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'label']
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.label


class SubCategory(models.Model):
    id = models.CharField(max_length=100, primary_key=True)
    category = models.ForeignKey(Category, related_name='subcategories', on_delete=models.CASCADE)
    label = models.CharField(max_length=150)
    slug = models.CharField(max_length=150, blank=True)
    description = models.TextField(blank=True)
    image = models.CharField(max_length=255, blank=True)
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'label']
        verbose_name_plural = 'Subcategories'

    def __str__(self):
        return f"{self.category.label} > {self.label}"


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
    subcategory = models.ForeignKey(SubCategory, related_name='products', on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    image = models.CharField(max_length=500, blank=True, default="/images/figure-samurai-red.svg")
    image_file = models.ImageField(upload_to='products/', blank=True, null=True)
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
        ordering = ['order', 'name']

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
    image_file = models.ImageField(upload_to='products/gallery/', blank=True, null=True)
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

