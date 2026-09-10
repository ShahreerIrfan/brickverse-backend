from django.db import models
from django.db.models import Sum, F, DecimalField, ExpressionWrapper
from apps.products.models import Product
from apps.users.models import User


class PartnerStore(models.Model):
    name = models.CharField(max_length=150)
    owner_name = models.CharField(max_length=150, blank=True)
    phone = models.CharField(max_length=50, blank=True)
    area = models.CharField(max_length=150, blank=True)     # e.g. "Mirpur, Dhaka"
    address = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    # ---- aggregates used everywhere in the UI; keep these as properties,
    # ---- do NOT cache/duplicate them onto columns ----
    @property
    def lines(self):
        return self.product_lines.all()

    @property
    def value_given(self):
        return self.lines.aggregate(
            v=Sum(F('qty_given') * F('tp_at_time'))
        )['v'] or 0

    @property
    def value_sold(self):
        return self.lines.aggregate(
            v=Sum(F('qty_sold') * F('tp_at_time'))
        )['v'] or 0

    @property
    def value_remaining(self):
        return self.lines.aggregate(
            v=Sum((F('qty_given') - F('qty_sold') - F('qty_returned')) * F('tp_at_time'))
        )['v'] or 0

    @property
    def total_paid(self):
        return self.payments.aggregate(v=Sum('amount'))['v'] or 0

    @property
    def amount_due(self):
        return self.value_sold - self.total_paid

    @property
    def settlement_status(self):
        """green=up_to_date, yellow=due_this_month, red=overdue"""
        due = self.amount_due
        if due <= 0:
            return 'up_to_date'
        from django.utils import timezone
        last_payment = self.payments.order_by('-payment_date').first()
        if not last_payment:
            return 'overdue' if due > 0 else 'up_to_date'
        days_since = (timezone.now().date() - last_payment.payment_date).days
        return 'overdue' if days_since > 30 else 'due_this_month'


class StoreProductLine(models.Model):
    """One row per (store, product) — running totals, not one row per event."""
    store = models.ForeignKey(PartnerStore, related_name='product_lines', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name='store_lines', on_delete=models.CASCADE)
    tp_at_time = models.DecimalField(
        max_digits=10, decimal_places=2,
        help_text="Snapshot of the product's Trade Price when first added to this store. "
                   "Never re-read Product.trade_price after this — TP can change later "
                   "and past transactions must stay historically accurate."
    )
    qty_given = models.PositiveIntegerField(default=0)
    qty_sold = models.PositiveIntegerField(default=0)
    qty_returned = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('store', 'product')
        ordering = ['-created_at']

    @property
    def qty_remaining(self):
        return self.qty_given - self.qty_sold - self.qty_returned

    @property
    def value_given(self):
        return self.qty_given * self.tp_at_time

    @property
    def value_sold(self):
        return self.qty_sold * self.tp_at_time

    def __str__(self):
        return f"{self.store.name} — {self.product.name}"


class StoreTransactionLog(models.Model):
    """Audit trail — one row per event. Never edited after creation."""
    EVENT_CHOICES = [
        ('given', 'Stock given'),
        ('sold', 'Sale recorded'),
        ('returned', 'Return recorded'),
    ]
    store = models.ForeignKey(PartnerStore, related_name='logs', on_delete=models.CASCADE)
    line = models.ForeignKey(StoreProductLine, related_name='logs', on_delete=models.CASCADE)
    event_type = models.CharField(max_length=20, choices=EVENT_CHOICES)
    quantity = models.PositiveIntegerField()
    note = models.CharField(max_length=255, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']


class StorePayment(models.Model):
    store = models.ForeignKey(PartnerStore, related_name='payments', on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField()
    method = models.CharField(max_length=50, default='cash', blank=True)
    note = models.CharField(max_length=255, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-payment_date', '-created_at']
