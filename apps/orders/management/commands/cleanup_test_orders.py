from django.core.management.base import BaseCommand
from django.db import transaction
from apps.orders.models import Order, OrderItem
from apps.products.models import Product

class Command(BaseCommand):
    help = "Safely clean up injected pentest test orders (Order 306, 307, 308, and test orders 298-308)"

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Scanning for test and injected pentest orders..."))

        # Injected test order IDs and known test signatures from report KWS-OI-2026-11-02
        target_ids = list(range(298, 309))  # 298 to 308 inclusive
        target_numbers = ["KS-C1F4A6"]

        found_orders = Order.objects.filter(
            id__in=target_ids
        ) | Order.objects.filter(
            order_number__in=target_numbers
        ) | Order.objects.filter(
            customer_name__icontains="IMPERSONATION TEST"
        )

        distinct_orders = list(found_orders.distinct())

        if not distinct_orders:
            self.stdout.write(self.style.SUCCESS("No injected pentest orders found. Database is clean!"))
            return

        self.stdout.write(f"Found {len(distinct_orders)} test order(s) to clean up:")
        with transaction.atomic():
            for o in distinct_orders:
                self.stdout.write(
                    f" - Order ID {o.id} (#{o.order_number}) | Email: {o.customer_email} | Name: {o.customer_name} | Amount: {o.total_amount}"
                )
                # Restock any deducted items if applicable
                for item in o.items.all():
                    if item.product and not item.is_preorder:
                        try:
                            prod = item.product
                            prod.stock = (prod.stock or 0) + item.quantity
                            prod.save(update_fields=['stock'])
                            self.stdout.write(f"   [Restocked] +{item.quantity} to '{prod.name}'")
                        except Exception as e:
                            self.stdout.write(self.style.WARNING(f"   [Restock Warning] Could not restock product {item.product_id}: {e}"))

                # Delete order items and order
                o.items.all().delete()
                o.delete()
                self.stdout.write(self.style.SUCCESS(f"   [Deleted] Order ID {o.id} removed successfully."))

        self.stdout.write(self.style.SUCCESS(f"Successfully cleaned up {len(distinct_orders)} test order(s)."))

