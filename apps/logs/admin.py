from django.contrib import admin
from django.contrib.admin.models import LogEntry, DELETION, ADDITION, CHANGE
from django.utils.html import format_html
from .models import SystemLog, LogRetentionSetting


@admin.register(LogEntry)
class LogEntryAdmin(admin.ModelAdmin):
    date_hierarchy = 'action_time'
    list_display = ('action_time', 'user', 'content_type', 'object_repr', 'action_flag_badge', 'change_message')
    list_filter = ('action_flag', 'content_type', 'user')
    search_fields = ('object_repr', 'change_message', 'user__username', 'user__email')
    readonly_fields = ('action_time', 'user', 'content_type', 'object_id', 'object_repr', 'action_flag', 'change_message')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    @admin.display(description="Action")
    def action_flag_badge(self, obj):
        if obj.action_flag == DELETION:
            return format_html('<span style="color: #ff3366; font-weight: bold;">🗑️ DELETED</span>')
        elif obj.action_flag == ADDITION:
            return format_html('<span style="color: #00cc66; font-weight: bold;">➕ ADDED</span>')
        elif obj.action_flag == CHANGE:
            return format_html('<span style="color: #3388ff; font-weight: bold;">✏️ CHANGED</span>')
        return obj.get_action_flag_display()


@admin.register(SystemLog)
class SystemLogAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'level', 'method', 'path', 'status_code', 'message_short')
    list_filter = ('level', 'status_code', 'method')
    search_fields = ('path', 'message', 'ip_address')
    readonly_fields = ('created_at', 'level', 'source', 'method', 'path', 'status_code', 'ip_address', 'user_agent', 'duration_ms', 'message', 'details', 'traceback')

    def message_short(self, obj):
        return obj.message[:80]
    message_short.short_description = 'Message'


@admin.register(LogRetentionSetting)
class LogRetentionSettingAdmin(admin.ModelAdmin):
    list_display = ('retention_days', 'is_auto_delete_enabled', 'last_cleaned_at', 'updated_at')
