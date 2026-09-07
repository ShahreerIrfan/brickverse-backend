from rest_framework import serializers
from .models import Announcement, HeroSlide, PromoCard, PromoBanner

class AnnouncementSerializer(serializers.ModelSerializer):
    highlightMessage = serializers.CharField(source='highlight_message')
    couponCode = serializers.CharField(source='coupon_code')

    class Meta:
        model = Announcement
        fields = ['id', 'message', 'highlightMessage', 'couponCode', 'is_active']


class HeroSlideSerializer(serializers.ModelSerializer):
    badgeText = serializers.CharField(source='badge_text')
    highlightWord = serializers.CharField(source='highlight_word')
    primaryBtnText = serializers.CharField(source='primary_btn_text')
    primaryBtnUrl = serializers.CharField(source='primary_btn_url')
    secondaryBtnText = serializers.CharField(source='secondary_btn_text')
    secondaryBtnUrl = serializers.CharField(source='secondary_btn_url')
    discountBadge = serializers.CharField(source='discount_badge')
    slideNumber = serializers.CharField(source='slide_number')

    class Meta:
        model = HeroSlide
        fields = [
            'id',
            'badgeText',
            'title',
            'highlightWord',
            'subtitle',
            'primaryBtnText',
            'primaryBtnUrl',
            'secondaryBtnText',
            'secondaryBtnUrl',
            'discountBadge',
            'image',
            'slideNumber',
            'order',
        ]


class PromoCardSerializer(serializers.ModelSerializer):
    badgeText = serializers.CharField(source='badge_text')
    highlightWord = serializers.CharField(source='highlight_word')
    buttonText = serializers.CharField(source='button_text')
    buttonUrl = serializers.CharField(source='button_url')
    hasTimer = serializers.BooleanField(source='has_timer')
    timer = serializers.SerializerMethodField()
    gradientType = serializers.CharField(source='gradient_type')

    class Meta:
        model = PromoCard
        fields = [
            'id',
            'card_type',
            'badgeText',
            'title',
            'highlightWord',
            'subtitle',
            'buttonText',
            'buttonUrl',
            'image',
            'hasTimer',
            'timer',
            'gradientType',
            'order',
        ]

    def get_timer(self, obj):
        if not obj.has_timer:
            return None
        return [
            {"value": obj.timer_days, "label": "days"},
            {"value": obj.timer_hours, "label": "hrs"},
            {"value": obj.timer_minutes, "label": "min"},
            {"value": obj.timer_seconds, "label": "sec"},
        ]


class PromoBannerSerializer(serializers.ModelSerializer):
    badgeText = serializers.CharField(source='badge_text')
    buttonText = serializers.CharField(source='button_text')
    buttonUrl = serializers.CharField(source='button_url')
    imageLeft = serializers.CharField(source='image_left')
    imageRight = serializers.CharField(source='image_right')

    class Meta:
        model = PromoBanner
        fields = [
            'id',
            'badgeText',
            'title',
            'subtitle',
            'buttonText',
            'buttonUrl',
            'imageLeft',
            'imageRight',
        ]
