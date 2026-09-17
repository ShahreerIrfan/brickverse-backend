from django.contrib import admin
from .models import Category, Tag, BlogPost, ContentBlock


class ContentBlockInline(admin.TabularInline):
    model = ContentBlock
    extra = 1
    ordering = ('order',)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'created_at')
    search_fields = ('name', 'slug')


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name', 'slug')


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'status', 'category', 'author', 'published_at', 'created_at')
    list_editable = ('status',)
    list_filter = ('status', 'category')
    search_fields = ('title', 'excerpt')
    inlines = [ContentBlockInline]
