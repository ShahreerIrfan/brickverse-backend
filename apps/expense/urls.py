from django.urls import path
from .views import (
    ExpenseListCreateView,
    ExpenseDetailView,
    ExpenseCategoryChoicesView,
    ExpenseSummaryView,
)

urlpatterns = [
    path('', ExpenseListCreateView.as_view(), name='expense-list-create'),
    path('summary/', ExpenseSummaryView.as_view(), name='expense-summary'),
    path('categories/', ExpenseCategoryChoicesView.as_view(), name='expense-categories'),
    path('<int:pk>/', ExpenseDetailView.as_view(), name='expense-detail'),
]
