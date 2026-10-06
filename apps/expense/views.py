from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Sum, Count
from django.utils import timezone
from .models import Expense, EPENSE_LIST_CHOICES
from .serializers import ExpenseSerializer

class ExpenseListCreateView(generics.ListCreateAPIView):
    """List all expenses or create a new expense."""
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
    queryset = Expense.objects.all()
    serializer_class = ExpenseSerializer


class ExpenseCategoryChoicesView(APIView):
    """Return available expense category choices for dropdowns."""
    def get(self, request):
        choices = [{"value": val, "label": label} for val, label in EPENSE_LIST_CHOICES]
        return Response(choices)


class ExpenseSummaryView(APIView):
    """Return aggregate statistics for expenses (Total, Monthly, Category Breakdown)."""
    def get(self, request):
        now = timezone.now()
        this_month_start = now.date().replace(day=1)

        total_expense = Expense.objects.aggregate(total=Sum('amount'))['total'] or 0
        this_month_expense = Expense.objects.filter(date__gte=this_month_start).aggregate(total=Sum('amount'))['total'] or 0
        total_count = Expense.objects.count()

        # Category Breakdown
        breakdown = Expense.objects.values('expense_title').annotate(
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
            "total_expense": float(total_expense),
            "this_month_expense": float(this_month_expense),
            "total_count": total_count,
            "category_breakdown": category_stats,
        })
