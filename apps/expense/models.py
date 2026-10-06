from django.db import models
from django.conf import settings

EPENSE_LIST_CHOICES = (
    ('SOCIAL_MEDIA_AD_COST', 'social media ad cost'),
    ('PACKAGING_MATERIAL', 'packaging material'),
    ('PR_AND_ADVERTISEMENT', 'pr and advertisement'),
    ('TRANSPORT', 'transport'),
    ('OTHER_EXPENSE', 'other expense'),
)

class Expense(models.Model):
    expense_title = models.CharField(max_length=100, choices=EPENSE_LIST_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField(auto_now_add=True)
    description = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='expenses'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-id']

    def __str__(self):
        return f"{self.get_expense_title_display()} - ৳{self.amount}"
