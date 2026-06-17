from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from budgets.models import Budget
from budgets.utils import get_budget_status
from categories.models import Category
from transactions.models import Transaction

User = get_user_model()


class BudgetStatusTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='alice', password='pass12345!')
        self.category = Category.objects.create(user=self.user, name='Groceries', type=Category.EXPENSE)
        self.budget = Budget.objects.create(user=self.user, category=self.category, monthly_limit=Decimal('100.00'))

    def _spend(self, amount, day='2026-06-10'):
        Transaction.objects.create(
            user=self.user, category=self.category, type='EXPENSE',
            amount=Decimal(amount), date=day,
        )

    def test_status_ok_below_80_percent(self):
        self._spend('50.00')
        status = get_budget_status(self.budget, year=2026, month=6)
        self.assertEqual(status['status'], 'OK')
        self.assertEqual(status['percent_used'], 50.0)

    def test_status_warning_at_80_percent(self):
        self._spend('80.00')
        status = get_budget_status(self.budget, year=2026, month=6)
        self.assertEqual(status['status'], 'WARNING')

    def test_status_exceeded_over_100_percent(self):
        self._spend('120.00')
        status = get_budget_status(self.budget, year=2026, month=6)
        self.assertEqual(status['status'], 'EXCEEDED')

    def test_only_counts_relevant_month(self):
        self._spend('90.00', day='2026-05-10')  # different month
        status = get_budget_status(self.budget, year=2026, month=6)
        self.assertEqual(status['status'], 'OK')
        self.assertEqual(status['spent'], Decimal('0.00'))

    def test_budget_on_income_category_rejected(self):
        income_cat = Category.objects.create(user=self.user, name='Salary', type=Category.INCOME)
        self.client.force_authenticate(self.user)
        resp = self.client.post('/api/budgets/', {'category': income_cat.id, 'monthly_limit': '100.00'})
        self.assertEqual(resp.status_code, 400)
