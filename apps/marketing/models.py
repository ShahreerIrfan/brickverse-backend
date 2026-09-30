from django.db import models

class NewsletterSubscriber(models.Model):
    email = models.EmailField(unique=True)
    source = models.CharField(max_length=50, default="footer_banner")
    subscribed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email


class NavLink(models.Model):
    label = models.CharField(max_length=100)
    url = models.CharField(max_length=200, default="#")
    is_active = models.BooleanField(default=False)
    is_hot = models.BooleanField(default=False)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.label


class StoreInfo(models.Model):
    name = models.CharField(max_length=100, default="Kawaii Subete")
    tagline = models.CharField(max_length=150, default="figures · bricks · code kits")
    phone = models.CharField(max_length=50, default="1800 246 010")
    email = models.EmailField(default="", blank=True)
    address = models.TextField(default="", blank=True)
    about_text = models.TextField(default="", blank=True)
    facebook_url = models.CharField(max_length=200, default="#", blank=True)
    instagram_url = models.CharField(max_length=200, default="#", blank=True)
    linkedin_url = models.CharField(max_length=200, default="#", blank=True)
    youtube_url = models.CharField(max_length=200, default="#", blank=True)

    def __str__(self):
        return self.name


class FooterColumn(models.Model):
    title = models.CharField(max_length=100)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.title


class FooterLink(models.Model):
    column = models.ForeignKey(FooterColumn, related_name='links', on_delete=models.CASCADE)
    label = models.CharField(max_length=100)
    url = models.CharField(max_length=200, default="#")
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.column.title} - {self.label}"


class HeroSlide(models.Model):
    title = models.CharField(max_length=200)
    subtitle = models.CharField(max_length=300, blank=True)
    button_text = models.CharField(max_length=50, blank=True, default="Shop now")
    button_link = models.CharField(max_length=300, blank=True, default="#")
    image = models.FileField(upload_to='hero_slides/', blank=True, null=True)
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return self.title


class ContactMessage(models.Model):
    name = models.CharField(max_length=150)
    email = models.EmailField()
    subject = models.CharField(max_length=200, blank=True)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Message from {self.name} ({self.email})"


class Coupon(models.Model):
    DISCOUNT_TYPES = [
        ('percentage', 'Percentage (%)'),
        ('fixed', 'Fixed Amount (৳)'),
    ]

    code = models.CharField(max_length=50, unique=True, db_index=True)
    description = models.CharField(max_length=255, blank=True, default='')
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPES, default='percentage')
    value = models.DecimalField(max_digits=10, decimal_places=2)
    min_order_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=True, null=True)
    max_discount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    usage_limit = models.PositiveIntegerField(blank=True, null=True)
    per_user_limit = models.PositiveIntegerField(default=1, blank=True, null=True)
    times_used = models.PositiveIntegerField(default=0)
    start_date = models.DateTimeField(blank=True, null=True)
    end_date = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.code} ({self.get_discount_type_display()} - {self.value})"

    def is_valid_now(self):
        from django.utils import timezone
        now = timezone.now()
        if not self.is_active:
            return False, "Coupon is currently disabled."
        if self.start_date and now < self.start_date:
            return False, "Coupon is not yet active."
        if self.end_date and now > self.end_date:
            return False, "Coupon has expired."
        if self.usage_limit is not None and self.usage_limit > 0 and self.times_used >= self.usage_limit:
            return False, "Coupon usage limit has been reached."
        return True, "Valid"

    def calculate_discount(self, subtotal):
        subtotal = float(subtotal)
        min_order = float(self.min_order_amount or 0)
        if subtotal < min_order:
            return 0, f"Minimum order amount of ৳{min_order:,.2f} required."

        if self.discount_type == 'percentage':
            discount = subtotal * (float(self.value) / 100.0)
            if self.max_discount is not None:
                max_disc = float(self.max_discount)
                if max_disc > 0 and discount > max_disc:
                    discount = max_disc
        else:  # fixed
            discount = float(self.value)
            if discount > subtotal:
                discount = subtotal

        return round(discount, 2), None
