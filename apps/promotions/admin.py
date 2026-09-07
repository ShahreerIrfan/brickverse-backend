from django.contrib import admin
from .models import Announcement, HeroSlide, PromoCard, PromoBanner

@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('message', 'coupon_code', 'is_active')
    list_editable = ('is_active',)


@admin.register(HeroSlide)
class HeroSlideAdmin(admin.ModelAdmin):
    list_display = ('title', 'badge_text', 'slide_number', 'order', 'is_active')
    list_editable = ('order', 'is_active')
    search_fields = ('title', 'badge_text', 'subtitle')


@admin.register(PromoCard)
class PromoCardAdmin(admin.ModelAdmin):
    list_display = ('title', 'card_type', 'badge_text', 'has_timer', 'order', 'is_active')
    list_editable = ('order', 'is_active')
    list_filter = ('card_type', 'has_timer', 'is_active')
    search_fields = ('title', 'badge_text')


@admin.register(PromoBanner)
class PromoBannerAdmin(admin.ModelAdmin):
    list_display = ('title', 'badge_text', 'button_text', 'is_active')
    list_editable = ('is_active',)
    search_fields = ('title', 'badge_text')
