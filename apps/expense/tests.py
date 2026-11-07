import datetime
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from apps.expense.models import Expense

User = get_user_model()

class ExpenseDateRangeFilterTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_user(
            email="admin@kawaiisubete.com",
            password="Password123!",
            role="admin",
            is_staff=True,
            is_superuser=True,
        )
        self.client.force_authenticate(user=self.admin)

        # Create sample expenses on different dates
        Expense.objects.create(
            expense_title="SOCIAL_MEDIA_AD_COST",
            amount=500.00,
            date=datetime.date(2026, 10, 1),
            description="FB Ad Campaign 1"
        )
        Expense.objects.create(
            expense_title="PACKAGING_MATERIAL",
            amount=200.00,
            date=datetime.date(2026, 10, 15),
            description="Boxes and bubble wrap"
        )
        Expense.objects.create(
            expense_title="TRANSPORT",
            amount=150.00,
            date=datetime.date(2026, 11, 2),
            description="Courier pick up"
        )
        Expense.objects.create(
            expense_title="OTHER_EXPENSE",
            amount=100.00,
            date=datetime.date(2026, 11, 5),
            description="Stationery"
        )

    def test_expense_list_date_range_filter(self):
        # Filter for October only (2026-10-01 to 2026-10-31)
        res = self.client.get("/api/expenses/", {
            "start_date": "2026-10-01",
            "end_date": "2026-10-31"
        })
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data), 2)
        total_in_range = sum(float(item['amount']) for item in res.data)
        self.assertEqual(total_in_range, 700.00)

    def test_expense_summary_without_filter(self):
        # All time summary
        res = self.client.get("/api/expenses/summary/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["total_expense"], 950.00)
        self.assertEqual(res.data["total_count"], 4)
        self.assertFalse(res.data["is_filtered"])

    def test_expense_summary_with_date_range_filter(self):
        # Filter from Oct 10 to Nov 3 (should capture 200 + 150 = 350)
        res = self.client.get("/api/expenses/summary/", {
            "start_date": "2026-10-10",
            "end_date": "2026-11-03"
        })
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["total_expense"], 950.00) # all time is preserved
        self.assertEqual(res.data["filtered_expense"], 350.00) # filtered cost for that specific range!
        self.assertEqual(res.data["filtered_count"], 2)
        self.assertTrue(res.data["is_filtered"])

    def test_create_expense_with_custom_past_date(self):
        # Ensure user can create expense with specific date
        res = self.client.post("/api/expenses/", {
            "expense_title": "PR_AND_ADVERTISEMENT",
            "amount": "300.00",
            "date": "2026-09-20",
            "description": "Influencer marketing"
        })
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.data["date"], "2026-09-20")
        
        # Verify stored in DB with that exact date
        exp = Expense.objects.get(id=res.data["id"])
        self.assertEqual(str(exp.date), "2026-09-20")

    def test_update_expense_date_with_patch(self):
        # Create an expense with an initial date
        exp = Expense.objects.create(
            expense_title="OTHER_EXPENSE",
            amount=500.00,
            date=datetime.date(2026, 11, 7),
            description="Testing",
            created_by=self.admin
        )
        # Change the date to an earlier date
        res = self.client.patch(f"/api/expenses/{exp.id}/", {
            "date": "2026-10-25"
        })
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["date"], "2026-10-25")
        exp.refresh_from_db()
        self.assertEqual(str(exp.date), "2026-10-25")
        self.assertEqual(exp.created_by, self.admin)

    def test_update_expense_date_with_put(self):
        # Create an expense with an initial date
        exp = Expense.objects.create(
            expense_title="TRANSPORT",
            amount=350.00,
            date=datetime.date(2026, 11, 7),
            description="Delivery",
            created_by=self.admin
        )
        # Update via PUT with a different date
        res = self.client.put(f"/api/expenses/{exp.id}/", {
            "expense_title": "TRANSPORT",
            "amount": "400.00",
            "date": "2026-11-01",
            "description": "Updated delivery"
        })
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["date"], "2026-11-01")
        exp.refresh_from_db()
        self.assertEqual(str(exp.date), "2026-11-01")
        self.assertEqual(exp.created_by, self.admin)
