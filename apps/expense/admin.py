from django.contrib import admin
from .models import Expense

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('id', 'expense_title', 'amount', 'date', 'created_by', 'created_at')
    list_filter = ('expense_title', 'date')
    search_fields = ('description', 'expense_title')
    ordering = ('-date', '-id')
