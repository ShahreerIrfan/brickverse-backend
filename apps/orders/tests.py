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
