from django.core.management.base import BaseCommand
from django.db import transaction
from apps.orders.models import Order, OrderItem
from apps.products.models import Product

RECOVERED_ORDERS_DATA = [
    {
        "order_number": "KS-D1D2EA",
        "customer_name": "Ashraful Haque",
        "customer_phone": "01865454378",
        "customer_email": "01865454378@fb-customer.local",
        "shipping_address": "Madartek shorkarpara 114/2 basaboo, Dhaka (Source: Facebook Page)",
        "shipping_cost": 60.00,
        "status": "processing",
        "carrier": "Steadfast Courier (COD)",
        "items": [
            {
                "slug": "marvels-deadpool-building-blocks-setf3022",
                "name": "Marvel's Deadpool Building Blocks Set (F3022)",
                "quantity": 1,
                "fallback_price": 450.00,
            }
        ]
    },
    {
        "order_number": "KS-DAE793",
        "customer_name": "Sabit Hasan Farabi",
        "customer_phone": "01885012515",
        "customer_email": "shfhasanfarabi22@gmail.com",
        "shipping_address": "147/21/1 South pirerbag, 60 feet road, Dhaka , Dhaka",
        "shipping_cost": 60.00,
        "status": "processing",
        "carrier": "Steadfast Courier (COD)",
        "items": [
            {
                "slug": "pokmon-classic-character-series-high-quality-version-bulbasaur",
                "name": "Pokémon Classic Character Series (High Quality Version): Bulbasaur",
                "quantity": 1,
                "fallback_price": 550.00,
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
        "status": "pending",
        "carrier": "Steadfast Courier (COD)",
        "items": [
            {
                "slug": "cute-cat-plush-toy-with-bell-collargray",
                "name": "Cute Cat Plush Toy with Bell Collar (Black)",
                "quantity": 1,
                "fallback_price": 450.00,
            },
            {
                "slug": "compact-cat-design-faux-leather-pocket-walletdark-pink",
                "name": "Compact Cat Design Faux Leather Pocket Wallet (Dark Pink)",
                "quantity": 1,
                "fallback_price": 380.00,
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
        "status": "pending",
        "carrier": "Steadfast Courier (COD)",
        "items": [
            {
                "slug": "blue-rose-flower-building-blocks-set-botanical-display-model-no7235",
                "name": "Blue Rose Flower Building Blocks Set – Botanical Display Model (NO.7235)",
                "quantity": 1,
                "fallback_price": 520.00,
            },
            {
                "slug": "white-lily-flower-building-blocks-set-botanical-display-model-no7242",
                "name": "White Lily Flower Building Blocks Set – Botanical Display Model (NO.7242)",
                "quantity": 1,
                "fallback_price": 520.00,
            },
            {
                "slug": "pokmon-classic-character-series-high-quality-version-jigglypuff",
                "name": "Pokémon Classic Character Series (High Quality Version): Jigglypuff",
                "quantity": 1,
                "fallback_price": 550.00,
            }
        ]
    },
    {
        "order_number": "KS-098028",
        "customer_name": "Shahreer Irfan",
        "customer_phone": "01344260216",
        "customer_email": "kawaiisubete1@gmail.com",
        "shipping_address": "Kachua, Chandpur, Dhaka",
        "shipping_cost": 120.00,
        "status": "pending",
        "carrier": "Steadfast Courier (COD)",
        "items": [
            {
                "slug": "demon-slayer-palverse-chibi-action-figures-giyu-tomioka",
                "name": "Demon Slayer PalVerse Chibi Action Figures – Giyu Tomioka",
                "quantity": 1,
                "fallback_price": 650.00,
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
        "status": "cancelled",
        "carrier": "Steadfast Courier (COD)",
        "items": [
            {
                "slug": "one-piece-bricks-set",
                "name": "One Piece BRICKS Set",
                "quantity": 1,
                "fallback_price": 1200.00,
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
        "status": "cancelled",
        "carrier": "Steadfast Courier (COD)",
        "items": [
            {
                "slug": "black-pirate-ship-building-blocks-set-caribbean-series-display-ship-model-a1",
                "name": "Black Pirate Ship Building Blocks Set – Caribbean Series Display Ship Model (A1)",
                "quantity": 1,
                "fallback_price": 1450.00,
            }
        ]
    }
]


class Command(BaseCommand):
    help = "Restores the 7 deleted orders back into the database with accurate customer details and items"

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("==> Restoring recovered orders..."))
        created_count = 0
        updated_count = 0

        with transaction.atomic():
            for data in RECOVERED_ORDERS_DATA:
                order_num = data["order_number"]
                
                # Check if product prices can be resolved dynamically from catalog
                total_items_cost = 0.0
                resolved_items = []

                for it in data["items"]:
                    prod = Product.objects.filter(slug=it["slug"]).first()
                    if not prod:
                        prod = Product.objects.filter(name__iexact=it["name"]).first()
                    if not prod:
                        prod = Product.objects.filter(id=it["slug"]).first()

                    # Calculate unit price
                    unit_price = it["fallback_price"]
                    if prod:
                        raw = prod.discounted_price or prod.price or prod.regular_price
                        try:
                            unit_price = float(str(raw).replace('৳', '').replace('$', '').replace(',', '').strip() or unit_price)
                        except Exception:
                            pass

                    bundle_items = []
                    if prod and prod.is_grouped:
                        bundle_items = [
                            {"name": gi.child.name, "quantity": gi.quantity}
                            for gi in prod.group_items.select_related('child')
                        ]

                    total_items_cost += unit_price * it["quantity"]
                    resolved_items.append({
                        "product": prod,
                        "name": prod.name if prod else it["name"],
                        "price": unit_price,
                        "quantity": it["quantity"],
                        "bundle_items": bundle_items,
                    })

                total_amount = total_items_cost + data["shipping_cost"]

                order, created = Order.objects.get_or_create(
                    order_number=order_num,
                    defaults={
                        "customer_name": data["customer_name"],
                        "customer_phone": data["customer_phone"],
                        "customer_email": data["customer_email"],
                        "shipping_address": data["shipping_address"],
                        "shipping_cost": data["shipping_cost"],
                        "total_amount": total_amount,
                        "status": data["status"],
                        "carrier": data["carrier"],
                    }
                )

                if created:
                    created_count += 1
                else:
                    # Update fields if already exists
                    order.customer_name = data["customer_name"]
                    order.customer_phone = data["customer_phone"]
                    order.customer_email = data["customer_email"]
                    order.shipping_address = data["shipping_address"]
                    order.shipping_cost = data["shipping_cost"]
                    order.total_amount = total_amount
                    order.status = data["status"]
                    order.carrier = data["carrier"]
                    order.save()
                    updated_count += 1

                # Recreate items
                OrderItem.objects.filter(order=order).delete()
                for ri in resolved_items:
                    OrderItem.objects.create(
                        order=order,
                        product=ri["product"],
                        product_name=ri["name"],
                        price=ri["price"],
                        quantity=ri["quantity"],
                        bundle_items=ri["bundle_items"],
                    )

                self.stdout.write(self.style.SUCCESS(f"  ✓ Processed Order #{order_num} ({order.customer_name}) - ৳{total_amount:,.2f}"))

        self.stdout.write(self.style.SUCCESS(f"\n==> Done! Created: {created_count}, Updated: {updated_count} order(s)."))
