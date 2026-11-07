from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Sum, Count
from django.utils import timezone
from .models import Expense, EPENSE_LIST_CHOICES
from .serializers import ExpenseSerializer
from apps.users.permissions import IsAdminRole

class ExpenseListCreateView(generics.ListCreateAPIView):
    """List all expenses or create a new expense."""
    permission_classes = [IsAdminRole]
    serializer_class = ExpenseSerializer
    pagination_class = None

    def get_queryset(self):
        queryset = Expense.objects.all().select_related('created_by').order_by('-date', '-id')
        category = self.request.query_params.get('category', '').strip()
        search = self.request.query_params.get('search', '').strip()
        start_date = self.request.query_params.get('start_date', '').strip()
        end_date = self.request.query_params.get('end_date', '').strip()

        if category and category != 'all':
            queryset = queryset.filter(expense_title=category)
        if search:
            queryset = queryset.filter(description__icontains=search)
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        return queryset

    def perform_create(self, serializer):
        user = self.request.user if self.request.user and self.request.user.is_authenticated else None
        serializer.save(created_by=user)


class ExpenseDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a single expense."""
    permission_classes = [IsAdminRole]
    queryset = Expense.objects.all()
    serializer_class = ExpenseSerializer


class ExpenseCategoryChoicesView(APIView):
    """Return available expense category choices for dropdowns."""
    permission_classes = [IsAdminRole]
    def get(self, request):
        choices = [{"value": val, "label": label} for val, label in EPENSE_LIST_CHOICES]
        return Response(choices)


class ExpenseSummaryView(APIView):
    """Return aggregate statistics for expenses (Total, Monthly, Date Range Filtered, Category Breakdown)."""
    permission_classes = [IsAdminRole]
    def get(self, request):
        now = timezone.now()
        this_month_start = now.date().replace(day=1)

        category = request.query_params.get('category', '').strip()
        search = request.query_params.get('search', '').strip()
        start_date = request.query_params.get('start_date', '').strip()
        end_date = request.query_params.get('end_date', '').strip()

        # All-time and this-month baseline metrics
        all_time_total = Expense.objects.aggregate(total=Sum('amount'))['total'] or 0
        this_month_expense = Expense.objects.filter(date__gte=this_month_start).aggregate(total=Sum('amount'))['total'] or 0
        all_time_count = Expense.objects.count()

        # Filtered queryset based on date range, category, search
        filtered_qs = Expense.objects.all()
        is_filtered = bool(start_date or end_date or (category and category != 'all') or search)

        if category and category != 'all':
            filtered_qs = filtered_qs.filter(expense_title=category)
        if search:
            filtered_qs = filtered_qs.filter(description__icontains=search)
        if start_date:
            filtered_qs = filtered_qs.filter(date__gte=start_date)
        if end_date:
            filtered_qs = filtered_qs.filter(date__lte=end_date)

        filtered_expense = filtered_qs.aggregate(total=Sum('amount'))['total'] or 0
        filtered_count = filtered_qs.count()

        # Category Breakdown for the active scope (or all-time if not filtered)
        breakdown_qs = filtered_qs if is_filtered else Expense.objects.all()
        breakdown = breakdown_qs.values('expense_title').annotate(
            total_amount=Sum('amount'),
            count=Count('id')
        ).order_by('-total_amount')

        choices_map = dict(EPENSE_LIST_CHOICES)
        category_stats = [
            {
                "category": item['expense_title'],
                "label": choices_map.get(item['expense_title'], item['expense_title']),
                "total_amount": float(item['total_amount'] or 0),
                "count": item['count'],
            }
            for item in breakdown
        ]

        return Response({
            "total_expense": float(all_time_total),
            "this_month_expense": float(this_month_expense),
            "total_count": all_time_count,
            "filtered_expense": float(filtered_expense),
            "filtered_count": filtered_count,
            "is_filtered": is_filtered,
            "start_date": start_date or None,
            "end_date": end_date or None,
            "category_breakdown": category_stats,
        })
