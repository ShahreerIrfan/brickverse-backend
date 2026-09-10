from django.contrib import admin
from .models import PartnerStore, StoreProductLine, StoreTransactionLog, StorePayment


class StoreProductLineInline(admin.TabularInline):
    model = StoreProductLine
    extra = 0
    readonly_fields = ('qty_remaining', 'value_given', 'value_sold')


class StorePaymentInline(admin.TabularInline):
    model = StorePayment
    extra = 0


@admin.register(PartnerStore)
class PartnerStoreAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner_name', 'area', 'phone', 'is_active', 'created_at')
    search_fields = ('name', 'owner_name', 'area', 'phone')
    list_filter = ('is_active',)
    inlines = [StoreProductLineInline, StorePaymentInline]


@admin.register(StoreTransactionLog)
class StoreTransactionLogAdmin(admin.ModelAdmin):
    list_display = ('store', 'line', 'event_type', 'quantity', 'created_at')
    list_filter = ('event_type', 'created_at')
    search_fields = ('store__name',)
