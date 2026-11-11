import json
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from apps.users.authentication import generate_user_token
from apps.products.models import Product, Category
from apps.orders.models import Order, OrderItem

User = get_user_model()


class OrderSecurityAndOwnershipTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Create Category & Product
        self.category = Category.objects.create(label="Anime Action Figures", slug="anime-action-figures")
        self.product = Product.objects.create(
            name="Goku Figure",
            slug="goku-figure",
            sku="GF-001",
            price="500.00",
            discounted_price="450.00",
            trade_price="300.00",
            stock=10,
            category=self.category,
        )

        # Create legitimate customer user
        self.customer = User.objects.create_user(
            email="legit_customer@example.com",
            password="SecurePassword123!",
            first_name="Legit",
            last_name="Customer",
            role=User.ROLE_CUSTOMER,
        )
        self.customer_token = generate_user_token(self.customer)

        # Create victim user
        self.victim = User.objects.create_user(
            email="victim_user@example.com",
            password="SecurePassword123!",
            first_name="Victim",
            last_name="User",
            role=User.ROLE_CUSTOMER,
        )
        self.victim_token = generate_user_token(self.victim)

        # Create admin user
        self.admin = User.objects.create_superuser(
            email="store_admin@kawaiisubete.com",
            password="AdminPassword123!",
            role=User.ROLE_ADMIN,
        )
        self.admin_token = generate_user_token(self.admin)

        # Pre-seed an order belonging to victim
        self.victim_order = Order.objects.create(
            order_number="KS-VICTIM01",
            customer_name="Victim User",
            customer_email=self.victim.email,
            customer_phone="01711111111",
            shipping_address="Dhanmondi, Dhaka",
            total_amount=510.00,
            shipping_cost=60.00,
            status="delivered",
        )
        OrderItem.objects.create(
            order=self.victim_order,
            product=self.product,
            product_name=self.product.name,
            price=450.00,
            quantity=1,
            trade_price="300.00",
        )

    def test_unauthenticated_post_order_rejected(self):
        """Unauthenticated order creation must be rejected with 401."""
        payload = {
            "items": [{"productId": self.product.id, "quantity": 1}],
            "customer_phone": "01700000000",
            "address": "Banani, Dhaka",
        }
        res = self.client.post("/api/orders/list/", data=json.dumps(payload), content_type="application/json")
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_empty_order_payload_rejected(self):
        """Sending empty payload {} or 0 items must be rejected."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.customer_token}")
        res = self.client.post("/api/orders/list/", data=json.dumps({}), content_type="application/json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("at least one item", res.data.get("error", ""))

    def test_cross_account_order_injection_forbidden(self):
        """
        Customer A authenticated as legit_customer attempts to submit an order
        with customer_email set to victim_user@example.com. Must be rejected with 403 Forbidden!
        """
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.customer_token}")
        injection_payload = {
            "customer_email": self.victim.email,
            "customer_name": "IMPERSONATION ATTACK",
            "customer_phone": "01899999999",
            "address": "Gulshan, Dhaka",
            "items": [{"productId": self.product.id, "quantity": 1, "price": 450.00}],
        }
        res = self.client.post("/api/orders/list/", data=json.dumps(injection_payload), content_type="application/json")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("forbidden", res.data.get("error", "").lower())

        # Verify no fake order was created for victim
        victim_orders = Order.objects.filter(customer_email=self.victim.email)
        self.assertEqual(victim_orders.count(), 1)
        self.assertEqual(victim_orders.first().order_number, "KS-VICTIM01")

    def test_legitimate_customer_order_creation_success(self):
        """Authenticated customer creates order with their own email or omitted email."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.customer_token}")
        payload = {
            "customer_name": "Legit Customer",
            "customer_phone": "01722222222",
            "address": "Mirpur 10, Dhaka",
            "items": [{"productId": self.product.id, "quantity": 1, "price": 450.00}],
        }
        res = self.client.post("/api/orders/list/", data=json.dumps(payload), content_type="application/json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data["customer_email"], self.customer.email)

        # Verify stock was deducted
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 9)

    def test_unauthenticated_order_list_snooping_rejected(self):
        """Unauthenticated request with ?email=victim@example.com must return 401."""
        res = self.client.get(f"/api/orders/list/?email={self.victim.email}")
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cross_account_order_list_forbidden(self):
        """Customer A authenticated tries to view Customer B's order via ?email= param."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.customer_token}")
        res = self.client.get(f"/api/orders/list/?email={self.victim.email}")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_dedicated_mine_endpoint_isolation(self):
        """GET /api/orders/mine/ returns strictly the authenticated user's orders."""
        # Check victim gets their order
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.victim_token}")
        res = self.client.get("/api/orders/mine/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["order_number"], "KS-VICTIM01")

        # Check customer gets empty list initially
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.customer_token}")
        res = self.client.get("/api/orders/mine/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 0)

    def test_cogs_and_profit_redacted_for_customers(self):
        """Trade price (total_tp) and net income must never be exposed to customer accounts."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.victim_token}")
        res = self.client.get("/api/orders/mine/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        order_data = res.data[0]
        self.assertNotIn("net_income", order_data)
        self.assertNotIn("netIncome", order_data)
        self.assertNotIn("total_tp", order_data)
        if "items" in order_data and len(order_data["items"]) > 0:
            self.assertNotIn("trade_price", order_data["items"][0])

    def test_admin_full_access_and_custom_order(self):
        """Admin can view all orders (including profit stats) and create custom walk-in orders."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.admin_token}")
        res = self.client.get("/api/orders/list/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(res.data), 1)
        admin_order_data = res.data[0]
        self.assertIn("net_income", admin_order_data)
        self.assertIn("total_tp", admin_order_data)

        # Admin creating custom order for a walk-in / phone customer
        custom_payload = {
            "customer_name": "Walk-in Phone Buyer",
            "customer_phone": "01733333333",
            "customer_email": "walkin@example.com",
            "address": "Uttara, Dhaka",
            "items": [{"productId": self.product.id, "quantity": 1, "price": 450.00}],
        }
        create_res = self.client.post("/api/orders/list/", data=json.dumps(custom_payload), content_type="application/json")
        self.assertEqual(create_res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(create_res.data["customer_email"], "walkin@example.com")

    def test_admin_can_edit_all_order_fields(self):
        """Admin can edit customer info, address, tracking, carrier, status, cost, and items."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.admin_token}")
        order_item = self.victim_order.items.first()
        patch_payload = {
            "customer_name": "Updated Customer Name",
            "customer_email": "updated_email@example.com",
            "customer_phone": "01999999999",
            "shipping_address": "House 10, Road 5, Banani, Dhaka",
            "shipping_cost": "120.00",
            "total_amount": "620.00",
            "tracking_number": "STEADFAST-9988",
            "carrier": "Steadfast Courier",
            "status": "processing",
            "items": [
                {
                    "id": order_item.id,
                    "product_name": "Goku Ultra Instinct Figure",
                    "quantity": 2,
                    "price": "500.00"
                }
            ]
        }
        res = self.client.patch(
            f"/api/orders/{self.victim_order.id}/",
            data=json.dumps(patch_payload),
            content_type="application/json"
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.victim_order.refresh_from_db()
        self.assertEqual(self.victim_order.customer_name, "Updated Customer Name")
        self.assertEqual(self.victim_order.customer_email, "updated_email@example.com")
        self.assertEqual(self.victim_order.customer_phone, "01999999999")
        self.assertEqual(self.victim_order.shipping_address, "House 10, Road 5, Banani, Dhaka")
        self.assertEqual(float(self.victim_order.shipping_cost), 120.00)
        self.assertEqual(float(self.victim_order.total_amount), 620.00)
        self.assertEqual(self.victim_order.tracking_number, "STEADFAST-9988")
        self.assertEqual(self.victim_order.carrier, "Steadfast Courier")
        self.assertEqual(self.victim_order.status, "processing")

        order_item.refresh_from_db()
        self.assertEqual(order_item.product_name, "Goku Ultra Instinct Figure")
        self.assertEqual(order_item.quantity, 2)
        self.assertEqual(float(order_item.price), 500.00)

    def test_admin_edit_order_quantity_split_across_fifo_lots(self):
        """When admin increases item quantity and older lot is exhausted, the additional unit comes from the next lot at its lot price."""
        from apps.products.models import ProductLot
        lot_prod = Product.objects.create(
            name="Naruto Shippuden Figure",
            slug="naruto-shippuden-figure",
            sku="NSF-001",
            price="270.00",
            category=self.category,
        )
        lot1 = ProductLot.objects.create(
            product=lot_prod,
            lot_number="LOT-20261111-001",
            trade_price="৳150.00",
            mrp="৳250.00",
            initial_quantity=3,
            remaining_quantity=0, # Customer bought all 3 from lot1
            is_active=True,
        )
        lot2 = ProductLot.objects.create(
            product=lot_prod,
            lot_number="LOT-20261111-002",
            trade_price="৳160.00",
            mrp="৳270.00",
            initial_quantity=5,
            remaining_quantity=5,
            is_active=True,
        )

        test_order = Order.objects.create(
            order_number="KS-LOTTEST01",
            customer_name="Test Buyer",
            customer_email="buyer@example.com",
            customer_phone="01722222222",
            shipping_address="Gulshan, Dhaka",
            shipping_cost=60.00,
            total_amount=810.00,
            status="processing",
        )
        first_item = OrderItem.objects.create(
            order=test_order,
            product=lot_prod,
            product_name=lot_prod.name,
            price=250.00,
            quantity=3,
            lot=lot1,
            lot_number=lot1.lot_number,
            trade_price=lot1.trade_price,
        )

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.admin_token}")
        patch_payload = {
            "items": [
                {
                    "id": first_item.id,
                    "product_id": lot_prod.id,
                    "quantity": 4, # Increasing from 3 to 4!
                }
            ]
        }
        res = self.client.patch(
            f"/api/orders/{test_order.id}/",
            data=json.dumps(patch_payload),
            content_type="application/json"
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # Check DB state
        order_items = list(test_order.items.order_by('id'))
        self.assertEqual(len(order_items), 2)

        # Item from Lot 1: 3 qty @ 250.00
        self.assertEqual(order_items[0].lot_id, lot1.id)
        self.assertEqual(order_items[0].quantity, 3)
        self.assertEqual(float(order_items[0].price), 250.00)

        # Item from Lot 2: 1 qty @ 270.00
        self.assertEqual(order_items[1].lot_id, lot2.id)
        self.assertEqual(order_items[1].quantity, 1)
        self.assertEqual(float(order_items[1].price), 270.00)

        # Lot 2 stock deducted from 5 to 4
        lot2.refresh_from_db()
        self.assertEqual(lot2.remaining_quantity, 4)

        # Total amount: 3*250 + 1*270 + 60 = 750 + 270 + 60 = 1080.00
        test_order.refresh_from_db()
        self.assertEqual(float(test_order.total_amount), 1080.00)

    def test_admin_order_edit_capped_by_stock_and_allowed_after_restock(self):
        """Admin cannot increase order quantity beyond available stock, but once restocked/new lot added, can increase."""
        from apps.products.models import ProductLot
        stock_prod = Product.objects.create(
            name="Limited Stock Collectible",
            slug="limited-stock-collectible",
            sku="LSC-001",
            price="100.00",
            category=self.category,
        )
        lot = ProductLot.objects.create(
            product=stock_prod,
            lot_number="LOT-20261111-LIMITED",
            trade_price="৳60.00",
            mrp="৳100.00",
            initial_quantity=3,
            remaining_quantity=2, # Total 3: 1 bought in order, 2 remaining in stock
            is_active=True,
        )

        order = Order.objects.create(
            order_number="KS-STOCKTEST01",
            customer_name="Stock Buyer",
            customer_email="stock_buyer@example.com",
            customer_phone="01733333333",
            shipping_address="Banani, Dhaka",
            shipping_cost=60.00,
            total_amount=160.00,
            status="pending",
        )
        item = OrderItem.objects.create(
            order=order,
            product=stock_prod,
            product_name=stock_prod.name,
            price=100.00,
            quantity=1,
            lot=lot,
            lot_number=lot.lot_number,
            trade_price=lot.trade_price,
        )

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.admin_token}")

        # Attempt 1: Try to increase quantity to 4 (which needs +3, but only 2 available in stock). Must be REJECTED!
        fail_payload = {
            "items": [
                {
                    "id": item.id,
                    "product_id": stock_prod.id,
                    "quantity": 4, # 1 original + 3 needed > 2 remaining
                }
            ]
        }
        fail_res = self.client.patch(
            f"/api/orders/{order.id}/",
            data=json.dumps(fail_payload),
            content_type="application/json"
        )
        self.assertEqual(fail_res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Only 2 additional unit(s) available in stock", fail_res.data["error"])

        # Attempt 2: Increase to 3 (which needs +2, exactly available in stock). Must SUCCEED!
        success_payload = {
            "items": [
                {
                    "id": item.id,
                    "product_id": stock_prod.id,
                    "quantity": 3, # 1 original + 2 needed == 2 remaining
                }
            ]
        }
        success_res = self.client.patch(
            f"/api/orders/{order.id}/",
            data=json.dumps(success_payload),
            content_type="application/json"
        )
        self.assertEqual(success_res.status_code, status.HTTP_200_OK)

        lot.refresh_from_db()
        self.assertEqual(lot.remaining_quantity, 0) # All stock now consumed

        # Attempt 3: Now remaining stock is 0. Try to increase from 3 to 4. Must be REJECTED!
        fail_res_2 = self.client.patch(
            f"/api/orders/{order.id}/",
            data=json.dumps(fail_payload),
            content_type="application/json"
        )
        self.assertEqual(fail_res_2.status_code, status.HTTP_400_BAD_REQUEST)

        # Attempt 4: Admin adds a new batch/lot (+5 units)
        new_lot = ProductLot.objects.create(
            product=stock_prod,
            lot_number="LOT-20261111-RESTOCK",
            trade_price="৳65.00",
            mrp="৳110.00",
            initial_quantity=5,
            remaining_quantity=5,
            is_active=True,
        )

        # Now trying to increase to 4 (needs +1 from the new lot) MUST SUCCEED!
        restock_payload = {
            "items": [
                {
                    "id": item.id,
                    "product_id": stock_prod.id,
                    "quantity": 4, # 3 from lot 1 + 1 from new_lot
                }
            ]
        }
        restock_res = self.client.patch(
            f"/api/orders/{order.id}/",
            data=json.dumps(restock_payload),
            content_type="application/json"
        )
        self.assertEqual(restock_res.status_code, status.HTTP_200_OK)

        new_lot.refresh_from_db()
        self.assertEqual(new_lot.remaining_quantity, 4)
