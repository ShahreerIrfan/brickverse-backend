from decimal import Decimal
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from apps.marketing.models import Coupon


class CouponValidationTests(APITestCase):
    def setUp(self):
        # Active 10% coupon, no min, no limit
        self.coupon_zubayer = Coupon.objects.create(
            code="ZUBAYER10",
            discount_type="percentage",
            value=Decimal("10.00"),
            min_order_amount=Decimal("0.00"),
            is_active=True,
        )

        # Active fixed 100 BDT coupon, min order 500
        self.coupon_fixed = Coupon.objects.create(
            code="FIXED100",
            discount_type="fixed",
            value=Decimal("100.00"),
            min_order_amount=Decimal("500.00"),
            is_active=True,
        )

        # Disabled coupon
        self.coupon_disabled = Coupon.objects.create(
            code="DISABLED10",
            discount_type="percentage",
            value=Decimal("10.00"),
            is_active=False,
        )

        # Expired coupon
        self.coupon_expired = Coupon.objects.create(
            code="EXPIRED10",
            discount_type="percentage",
            value=Decimal("10.00"),
            end_date=timezone.now() - timezone.timedelta(days=1),
            is_active=True,
        )

    def test_anonymous_user_can_validate_active_coupon(self):
        """Unauthenticated customer can validate coupon on checkout without 403."""
        response = self.client.post(
            "/api/coupons/validate/",
            {"code": "ZUBAYER10", "subtotal": 750},
            format="json",
            HTTP_HOST="api.kawaiisubete.com",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["valid"])
        self.assertEqual(response.data["code"], "ZUBAYER10")
        self.assertEqual(response.data["discount_amount"], 75.0)

    def test_case_insensitive_and_whitespace_trimming(self):
        """Coupon code matching is case-insensitive and trims whitespace."""
        response = self.client.post(
            "/api/coupons/validate/",
            {"code": "  zubayer10  ", "subtotal": 750},
            format="json",
            HTTP_HOST="api.kawaiisubete.com",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["valid"])
        self.assertEqual(response.data["discount_amount"], 75.0)

    def test_fixed_discount_with_min_order(self):
        # Subtotal below min order
        res_fail = self.client.post(
            "/api/coupons/validate/",
            {"code": "FIXED100", "subtotal": 400},
            format="json",
            HTTP_HOST="api.kawaiisubete.com",
        )
        self.assertEqual(res_fail.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Minimum order amount", res_fail.data["error"])

        # Subtotal meets min order
        res_ok = self.client.post(
            "/api/coupons/validate/",
            {"code": "FIXED100", "subtotal": 600},
            format="json",
            HTTP_HOST="api.kawaiisubete.com",
        )
        self.assertEqual(res_ok.status_code, status.HTTP_200_OK)
        self.assertEqual(res_ok.data["discount_amount"], 100.0)

    def test_disabled_coupon_rejected(self):
        response = self.client.post(
            "/api/coupons/validate/",
            {"code": "DISABLED10", "subtotal": 750},
            format="json",
            HTTP_HOST="api.kawaiisubete.com",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "Coupon is currently disabled.")

    def test_expired_coupon_rejected(self):
        response = self.client.post(
            "/api/coupons/validate/",
            {"code": "EXPIRED10", "subtotal": 750},
            format="json",
            HTTP_HOST="api.kawaiisubete.com",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "Coupon has expired.")

    def test_nonexistent_coupon_returns_404(self):
        response = self.client.post(
            "/api/coupons/validate/",
            {"code": "NONEXISTENT", "subtotal": 750},
            format="json",
            HTTP_HOST="api.kawaiisubete.com",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("not found", response.data["error"])

    def test_empty_coupon_code_rejected(self):
        response = self.client.post(
            "/api/coupons/validate/",
            {"code": "", "subtotal": 750},
            format="json",
            HTTP_HOST="api.kawaiisubete.com",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "Please provide a coupon code.")
