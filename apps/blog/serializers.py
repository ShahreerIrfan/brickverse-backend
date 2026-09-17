from django.conf import settings
from django.db import transaction
from rest_framework import serializers
from .models import Category, Tag, BlogPost, ContentBlock


def _resolve_featured_image(request):
    """Accepts either a multipart file upload (`featured_image`/`featuredImage`)
    or a plain `featuredImage` URL string in the JSON body — the admin editor
    uploads the file via /blog/media/upload/ first (same endpoint the
    in-content image/gallery blocks use) and just sends back the resulting
    URL here, rather than uploading the same bytes twice."""
    if not request:
        return None

    if hasattr(request, 'FILES'):
        img_upload = request.FILES.get('featured_image') or request.FILES.get('featuredImage')
        if img_upload:
            return img_upload

    value = None
    if hasattr(request, 'data'):
        value = request.data.get('featuredImage') or request.data.get('featured_image')
    if isinstance(value, str) and value:
        media_url = settings.MEDIA_URL
        idx = value.find(media_url)
        return value[idx + len(media_url):] if idx != -1 else value.lstrip('/')

    return None


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'created_at']
        extra_kwargs = {
            'slug': {'required': False, 'allow_blank': True},
        }


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name', 'slug']
        extra_kwargs = {
            'slug': {'required': False, 'allow_blank': True},
        }


class ContentBlockSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    blockType = serializers.CharField(source='block_type')

    class Meta:
        model = ContentBlock
        fields = ['id', 'order', 'blockType', 'data']


class AuthorSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.SerializerMethodField()
    email = serializers.EmailField(read_only=True)

    def get_name(self, obj):
        full_name = f"{getattr(obj, 'first_name', '') or ''} {getattr(obj, 'last_name', '') or ''}".strip()
        return full_name or getattr(obj, 'email', '')


class BlogPostListSerializer(serializers.ModelSerializer):
    featuredImage = serializers.SerializerMethodField()
    publishedAt = serializers.DateTimeField(source='published_at', read_only=True)
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    updatedAt = serializers.DateTimeField(source='updated_at', read_only=True)
    category = CategorySerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    author = AuthorSerializer(read_only=True)

    class Meta:
        model = BlogPost
        fields = [
            'id',
            'title',
            'slug',
            'excerpt',
            'featuredImage',
            'status',
            'category',
            'tags',
            'author',
            'publishedAt',
            'createdAt',
            'updatedAt',
        ]

    def get_featuredImage(self, obj):
        img = obj.featured_image
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


class BlogPostDetailSerializer(serializers.ModelSerializer):
    featuredImage = serializers.SerializerMethodField()
    publishedAt = serializers.DateTimeField(source='published_at', required=False, allow_null=True)
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    updatedAt = serializers.DateTimeField(source='updated_at', read_only=True)
    category = CategorySerializer(read_only=True)
    categoryId = serializers.PrimaryKeyRelatedField(
        source='category', queryset=Category.objects.all(), write_only=True, required=False, allow_null=True
    )
    tags = TagSerializer(many=True, read_only=True)
    tagIds = serializers.PrimaryKeyRelatedField(
        source='tags', queryset=Tag.objects.all(), write_only=True, required=False, many=True
    )
    author = AuthorSerializer(read_only=True)
    blocks = ContentBlockSerializer(many=True, required=False)

    class Meta:
        model = BlogPost
        fields = [
            'id',
            'title',
            'slug',
            'excerpt',
            'featuredImage',
            'status',
            'category',
            'categoryId',
            'tags',
            'tagIds',
            'author',
            'publishedAt',
            'createdAt',
            'updatedAt',
            'blocks',
        ]
        extra_kwargs = {
            'slug': {'required': False, 'allow_blank': True},
        }

    def get_featuredImage(self, obj):
        img = obj.featured_image
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

    def _sync_blocks(self, post, blocks_data):
        incoming_ids = [b.get('id') for b in blocks_data if b.get('id')]
        post.blocks.exclude(id__in=incoming_ids).delete()

        for block in blocks_data:
            block_id = block.get('id')
            payload = {
                'order': block.get('order', 0),
                'block_type': block.get('block_type', ''),
                'data': block.get('data', {}),
            }
            if block_id:
                ContentBlock.objects.filter(id=block_id, post=post).update(**payload)
            else:
                ContentBlock.objects.create(post=post, **payload)

    def create(self, validated_data):
        tags = validated_data.pop('tags', None)
        blocks_data = validated_data.pop('blocks', [])

        request = self.context.get('request')
        resolved_image = _resolve_featured_image(request)
        if resolved_image is not None:
            validated_data['featured_image'] = resolved_image

        with transaction.atomic():
            instance = BlogPost.objects.create(**validated_data)
            if tags is not None:
                instance.tags.set(tags)
            self._sync_blocks(instance, blocks_data)

        return instance

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags', None)
        blocks_data = validated_data.pop('blocks', None)

        request = self.context.get('request')
        resolved_image = _resolve_featured_image(request)
        if resolved_image is not None:
            validated_data['featured_image'] = resolved_image

        with transaction.atomic():
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()

            if tags is not None:
                instance.tags.set(tags)
            if blocks_data is not None:
                self._sync_blocks(instance, blocks_data)

        return instance
