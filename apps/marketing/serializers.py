from rest_framework import serializers
from .models import NewsletterSubscriber, NavLink, StoreInfo, FooterColumn, FooterLink, ContactMessage, HeroSlide

class NewsletterSubscriberSerializer(serializers.ModelSerializer):
    class Meta:
        model = NewsletterSubscriber
        fields = ['id', 'email', 'source', 'subscribed_at']
        read_only_fields = ['id', 'subscribed_at']


class NavLinkSerializer(serializers.ModelSerializer):
    active = serializers.BooleanField(source='is_active')
    hot = serializers.BooleanField(source='is_hot')

    class Meta:
        model = NavLink
        fields = ['id', 'label', 'url', 'active', 'hot', 'order']


class StoreInfoSerializer(serializers.ModelSerializer):
    aboutText = serializers.CharField(source='about_text')
    social = serializers.SerializerMethodField()

    class Meta:
        model = StoreInfo
        fields = [
            'name',
            'tagline',
            'phone',
            'email',
            'address',
            'aboutText',
            'facebook_url',
            'instagram_url',
            'linkedin_url',
            'youtube_url',
            'social',
        ]

    def get_social(self, obj):
        return [
            {"platform": "f", "url": obj.facebook_url},
            {"platform": "in", "url": obj.linkedin_url},
            {"platform": "ig", "url": obj.instagram_url},
            {"platform": "yt", "url": obj.youtube_url},
        ]


class FooterLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = FooterLink
        fields = ['id', 'label', 'url', 'order']


class FooterColumnSerializer(serializers.ModelSerializer):
    links = serializers.SerializerMethodField()

    class Meta:
        model = FooterColumn
        fields = ['id', 'title', 'order', 'links']

    def get_links(self, obj):
        return [link.label for link in obj.links.all().order_by('order')]


class HeroSlideSerializer(serializers.ModelSerializer):
    buttonText = serializers.CharField(source='button_text', required=False, allow_blank=True)
    buttonLink = serializers.CharField(source='button_link', required=False, allow_blank=True)
    image = serializers.SerializerMethodField()
    image_file = serializers.FileField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = HeroSlide
        fields = [
            'id',
            'title',
            'subtitle',
            'button_text',
            'buttonText',
            'button_link',
            'buttonLink',
            'image',
            'image_file',
            'order',
            'is_active',
        ]

    def get_image(self, obj):
        img = obj.image
        if not img:
            return None
        try:
            url = img.url
        except Exception:
            return None
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(url)
        return url

    def create(self, validated_data):
        image_file = validated_data.pop('image_file', None)
        if image_file:
            validated_data['image'] = image_file
        return super().create(validated_data)

    def update(self, instance, validated_data):
        image_file = validated_data.pop('image_file', None)
        if image_file:
            validated_data['image'] = image_file
        return super().update(instance, validated_data)


class ContactMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactMessage
        fields = ['id', 'name', 'email', 'subject', 'message', 'created_at']
        read_only_fields = ['id', 'created_at']
