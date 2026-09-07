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
    name = models.CharField(max_length=100, default="Brickverse")
    tagline = models.CharField(max_length=150, default="figures · bricks · code kits")
    phone = models.CharField(max_length=50, default="1800 246 010")
    email = models.EmailField(default="hi@brickverse.com.au")
    address = models.TextField(default="14 Maribyrnong St, Footscray VIC 3011")
    about_text = models.TextField(default="Authentic anime figures, cartoon collectibles, brick sets and coding kits. Shipping Australia-wide from our Melbourne warehouse since 2019.")
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
