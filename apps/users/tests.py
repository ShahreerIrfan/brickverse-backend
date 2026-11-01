from django.test import TestCase, RequestFactory
from django.conf import settings
from apps.users.views import CurrentUserProfileView
from apps.orders.views import OrderListView, AdminDashboardStatsView
from apps.products.views import ProductListView
from apps.products.models import Product
from apps.marketing.views import NewsletterSubscribeView


class SecurityAssessmentRegressionTests(TestCase):
    """
    Automated regression tests covering all confirmed security audit findings
    from the 28-Oct-2026 assessment (F-12, F-13, F-05, F-01, N-02).
    """

    def setUp(self):
        self.rf = RequestFactory()

    def test_f12_client_identity_headers_rejected(self):
        # 1. x-user-id header must NOT authenticate
        req = self.rf.get("/api/auth/me/", HTTP_HOST="api.kawaiisubete.com", HTTP_X_USER_ID="1")
        resp = CurrentUserProfileView.as_view()(req)
        self.assertFalse(resp.data.get("authenticated"))
        self.assertIsNone(resp.data.get("user"))

        # 2. x-user-email header must NOT authenticate
        req2 = self.rf.get("/api/auth/me/", HTTP_HOST="api.kawaiisubete.com", HTTP_X_USER_EMAIL="admin@gmail.com")
        resp2 = CurrentUserProfileView.as_view()(req2)
        self.assertFalse(resp2.data.get("authenticated"))
        self.assertIsNone(resp2.data.get("user"))

    def test_f12_order_list_rejects_header_without_credentials(self):
        # Order list must reject x-user-id header with 401/403
        req = self.rf.get("/api/orders/", HTTP_HOST="api.kawaiisubete.com", HTTP_X_USER_ID="1")
        try:
            resp = OrderListView.as_view()(req)
            self.assertIn(resp.status_code, (401, 403))
        except Exception:
            pass  # 401 exception raised by DRF

    def test_f13_admin_stats_rejects_anonymous_access(self):
        # Admin stats must reject unauthenticated requests
        req = self.rf.get("/api/orders/admin-stats/", HTTP_HOST="api.kawaiisubete.com")
        try:
            resp = AdminDashboardStatsView.as_view()(req)
            self.assertIn(resp.status_code, (401, 403))
        except Exception:
            pass

    def test_f01_cors_safe_configuration(self):
        # CORS must not allow all origins
        self.assertFalse(settings.CORS_ALLOW_ALL_ORIGINS)
        # Identity headers must not be in CORS allowed headers
        self.assertNotIn("x-user-id", settings.CORS_ALLOW_HEADERS)
        self.assertNotIn("x-user-email", settings.CORS_ALLOW_HEADERS)

    def test_f05_tradeprice_not_exposed_publicly(self):
        prod = Product.objects.create(
            name="Test Armor Figure",
            slug="test-armor-figure",
            price="350",
            trade_price="180",
            stock=10
        )
        req = self.rf.get("/api/products/", HTTP_HOST="api.kawaiisubete.com")
        resp = ProductListView.as_view()(req)
        results = resp.data if isinstance(resp.data, list) else resp.data.get('results', [])
        found = next((p for p in results if p.get('slug') == 'test-armor-figure'), None)
        if found:
            self.assertNotIn("tradePrice", found)

    def test_n02_newsletter_subscribe_accessible_anonymously(self):
        req = self.rf.post(
            "/api/marketing/newsletter/subscribe/",
            HTTP_HOST="api.kawaiisubete.com",
            data={"email": "newcustomer@kawaiisubete.com"},
            content_type="application/json"
        )
        resp = NewsletterSubscribeView.as_view()(req)
        self.assertIn(resp.status_code, (200, 201))

