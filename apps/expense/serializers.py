from rest_framework import serializers
from .models import Expense, EPENSE_LIST_CHOICES

class ExpenseSerializer(serializers.ModelSerializer):
    expense_title_display = serializers.CharField(source='get_expense_title_display', read_only=True)
    created_by_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Expense
        fields = [
            'id',
            'expense_title',
            'expense_title_display',
            'amount',
            'date',
            'description',
            'created_by',
            'created_by_name',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_created_by_name(self, obj):
        if obj.created_by:
            first = getattr(obj.created_by, 'first_name', '') or ''
            last = getattr(obj.created_by, 'last_name', '') or ''
            full = f"{first} {last}".strip()
            return full or getattr(obj.created_by, 'email', 'Admin')
        return 'Admin'
