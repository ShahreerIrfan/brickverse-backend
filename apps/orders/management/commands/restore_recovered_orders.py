from django.core.management.base import BaseCommand
from django.db import transaction
from apps.orders.models import Order, OrderItem
from apps.products.models import Product

RECOVERED_ORDERS_DATA = [
    {
        "order_number": "KS-DAE793",
        "customer_name": "Sabit Hasan Farabi",
        "customer_phone": "01885012515",
        "customer_email": "shfhasanfarabi22@gmail.com",
        "shipping_address": "147/21/1 South pirerbag, 60 feet road, Dhaka , Dhaka",
        "shipping_cost": 60.00,
        "total_amount": 360.00,
        "status": "processing",
        "carrier": "Steadfast Courier (COD)",
        "items": [
            {
                "slug": "red-pirate-ship-building-blocks-set-caribbean-series-display-ship-model-a5",
                "name": "Red Pirate Ship Building Blocks Set – Caribbean Series Display Ship Model (A5)",
                "quantity": 1,
                "price": 300.00,
            }
        ]
    },
    {
        "order_number": "KS-D1D2EA",
        "customer_name": "Ashraful Haque",
        "customer_phone": "01865454378",
        "customer_email": "01865454378@fb-customer.local",
        "shipping_address": "Madartek shorkarpara 114/2 basaboo, Dhaka (Source: Facebook Page)",
        "shipping_cost": 60.00,
        "total_amount": 360.00,
        "status": "processing",
        "carrier": "Steadfast Courier (COD)",
        "items": [
            {
                "slug": "black-pirate-ship-building-blocks-set-caribbean-series-display-ship-model-a1",
                "name": "Black Pirate Ship Building Blocks Set – Caribbean Series Display Ship Model (A1)",
                "quantity": 1,
                "price": 300.00,
            }
        ]
    },
    {
        "order_number": "KS-348BEE",
        "customer_name": "Nusrat Sara",
        "customer_phone": "01752543972",
        "customer_email": "sorowarjahan59@gmail.com",
        "shipping_address": "Sonirakra 24 ft rosulbug mosjid green tower building, kodomtali, dhaka , Dhaka",
        "shipping_cost": 60.00,
        "total_amount": 1110.00,
        "status": "pending",
        "carrier": "Steadfast Courier (COD)",
        "items": [
            {
                "slug": "windmill-cottage-building-blocks-set-red-architecture-house-model-mz-216",
                "name": "Windmill Cottage Building Blocks Set – Red Architecture House Model (MZ-216)",
                "quantity": 1,
                "price": 350.00,
            },
            {
                "slug": "ice-cream-vending-cart-building-blocks-set-cute-dessert-cart-diy-model-no-k400",
                "name": "Ice Cream Vending Cart Building Blocks Set – Cute Dessert Cart DIY Model (NO. K400)",
                "quantity": 1,
                "price": 350.00,
            },
            {
                "slug": "windmill-cottage-building-blocks-set-blue-architecture-house-model-mz-215",
                "name": "Windmill Cottage Building Blocks Set – Blue Architecture House Model (MZ-215)",
                "quantity": 1,
                "price": 350.00,
            }
        ]
    },
    {
        "order_number": "KS-B0BFE8",
        "customer_name": "Sarah Hossain",
        "customer_phone": "01757232943",
        "customer_email": "sarah251071066@gmail.com",
        "shipping_address": "House 44, road 13, sector 12, uttara dhaka, Dhaka",
        "shipping_cost": 60.00,
        "total_amount": 410.00,
        "status": "pending",
        "carrier": "Steadfast Courier (COD)",
        "items": [
            {
                "slug": "demon-slayer-palverse-chibi-action-figures-giyu-tomioka",
                "name": "Demon Slayer PalVerse Chibi Action Figures – Giyu Tomioka",
                "quantity": 1,
                "price": 350.00,
            }
        ]
    },
    {
        "order_number": "KS-1793DA",
        "customer_name": "MD Shahreer Irfan",
        "customer_phone": "01755074517",
        "customer_email": "mdshahreerirfan@gmail.com",
        "shipping_address": "Kachua, Chandpur (Source: Facebook Page)",
        "shipping_cost": 120.00,
        "total_amount": 1320.00,
        "status": "cancelled",
        "carrier": "Steadfast Courier (COD)",
        "items": [
            {
                "slug": "one-piece-bricks-set",
                "name": "One Piece BRICKS Set",
                "quantity": 1,
                "price": 1200.00,
            }
        ]
    },
    {
        "order_number": "KS-DC5848",
        "customer_name": "MD Irfan",
        "customer_phone": "01344260216",
        "customer_email": "mdshahreerirfan@gmail.com",
        "shipping_address": "Niketan Bazar, (Beside Lucky Khan Mosjid), Banani, Dhaka-1212., Dhaka",
        "shipping_cost": 60.00,
        "total_amount": 1510.00,
        "status": "cancelled",
        "carrier": "Steadfast Courier (COD)",
        "items": [
            {
                "slug": "black-pirate-ship-building-blocks-set-caribbean-series-display-ship-model-a1",
                "name": "Black Pirate Ship Building Blocks Set – Caribbean Series Display Ship Model (A1)",
                "quantity": 1,
                "price": 1450.00,
            }
        ]
    }
]


class Command(BaseCommand):
    help = "Restores all extracted deleted orders back into production database"

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("==> Seeding recovered orders to database..."))
        created_count = 0
        updated_count = 0

        with transaction.atomic():
            for data in RECOVERED_ORDERS_DATA:
                order_num = data["order_number"]

                order, created = Order.objects.get_or_create(
                    order_number=order_num,
                    defaults={
                        "customer_name": data["customer_name"],
                        "customer_phone": data["customer_phone"],
                        "customer_email": data["customer_email"],
                        "shipping_address": data["shipping_address"],
                        "shipping_cost": data["shipping_cost"],
                        "total_amount": data["total_amount"],
                        "status": data["status"],
                        "carrier": data["carrier"],
                    }
                )

                if created:
                    created_count += 1
                else:
                    order.customer_name = data["customer_name"]
                    order.customer_phone = data["customer_phone"]
                    order.customer_email = data["customer_email"]
                    order.shipping_address = data["shipping_address"]
                    order.shipping_cost = data["shipping_cost"]
                    order.total_amount = data["total_amount"]
                    order.status = data["status"]
                    order.carrier = data["carrier"]
                    order.save()
                    updated_count += 1

                # Recreate line items
                OrderItem.objects.filter(order=order).delete()
                for it in data["items"]:
                    prod = Product.objects.filter(slug=it["slug"]).first()
                    if not prod:
                        prod = Product.objects.filter(id=it["slug"]).first()
                    if not prod:
                        prod = Product.objects.filter(name__iexact=it["name"]).first()

                    bundle_items = []
                    if prod and prod.is_grouped:
                        bundle_items = [
                            {"name": gi.child.name, "quantity": gi.quantity}
                            for gi in prod.group_items.select_related('child')
                        ]

                    OrderItem.objects.create(
                        order=order,
                        product=prod,
                        product_name=it["name"],
                        price=it["price"],
                        quantity=it["quantity"],
                        bundle_items=bundle_items,
                        is_preorder=False,
                    )

                self.stdout.write(self.style.SUCCESS(f"  ✓ Seeded Order #{order_num} ({order.customer_name}) - ৳{order.total_amount}"))

        self.stdout.write(self.style.SUCCESS(f"\n==> Successfully seeded all {created_count + updated_count} orders!"))
