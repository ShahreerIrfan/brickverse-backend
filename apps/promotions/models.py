from django.db import models

class Announcement(models.Model):
    message = models.CharField(max_length=200, default="Free delivery over ৳500")
    highlight_message = models.CharField(max_length=255, default="Code BUILD10 saves you 10% on your first order")
    coupon_code = models.CharField(max_length=50, blank=True, default="BUILD10")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.message


class HeroSlide(models.Model):
    badge_text = models.CharField(max_length=100, default="✦ New season drop")
    title = models.CharField(max_length=200, default="Build your own universe.")
    highlight_word = models.CharField(max_length=50, default="universe.")
    subtitle = models.TextField(default="Anime figures, cartoon collectibles, brick sets & coding kits — shipped in 48h.")
    primary_btn_text = models.CharField(max_length=50, default="Shop now")
    primary_btn_url = models.CharField(max_length=200, default="#")
    secondary_btn_text = models.CharField(max_length=50, default="Explore sets")
    secondary_btn_url = models.CharField(max_length=200, default="#")
    discount_badge = models.CharField(max_length=50, default="40% OFF TODAY")
    image = models.CharField(max_length=255, default="/images/figure-samurai-red.svg")
    slide_number = models.CharField(max_length=20, default="01 / 03")
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.title


class PromoCard(models.Model):
    CARD_TYPES = [
        ('new_arrivals', 'New Arrivals'),
        ('deal_of_the_week', 'Deal of the Week'),
        ('custom', 'Custom'),
    ]
    card_type = models.CharField(max_length=50, choices=CARD_TYPES, default='new_arrivals')
    badge_text = models.CharField(max_length=100)
    title = models.CharField(max_length=200)
    highlight_word = models.CharField(max_length=50, blank=True)
    subtitle = models.CharField(max_length=255, blank=True)
    button_text = models.CharField(max_length=50, default="Shop now")
    button_url = models.CharField(max_length=200, default="#")
    image = models.CharField(max_length=255)
    has_timer = models.BooleanField(default=False)
    timer_days = models.CharField(max_length=10, default="02", blank=True)
    timer_hours = models.CharField(max_length=10, default="14", blank=True)
    timer_minutes = models.CharField(max_length=10, default="36", blank=True)
    timer_seconds = models.CharField(max_length=10, default="09", blank=True)
    gradient_type = models.CharField(max_length=50, default="purple")
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.badge_text} - {self.title}"


class PromoBanner(models.Model):
    badge_text = models.CharField(max_length=100, default="Weekend bundle")
    title = models.CharField(max_length=200, default="Buy any two brick sets, get a mini figure free")
    subtitle = models.TextField(default="Mix and match across bricks, robotics and STEM kits. Ends Sunday 11:59pm.")
    button_text = models.CharField(max_length=50, default="Shop bundle")
    button_url = models.CharField(max_length=200, default="#")
    image_left = models.CharField(max_length=255, default="/images/bricks-stack-sunny.svg")
    image_right = models.CharField(max_length=255, default="/images/toon-mascot.svg")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title
