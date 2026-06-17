from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from categories.models import Category
from transactions.models import Transaction

User = get_user_model()


class MonthlyAnalyticsTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='alice', password='pass12345!')
        self.client.force_authenticate(self.user)
        self.expense_cat = Category.objects.create(user=self.user, name='Groceries', type=Category.EXPENSE)
        self.income_cat = Category.objects.create(user=self.user, name='Salary', type=Category.INCOME)
        Transaction.objects.create(user=self.user, category=self.income_cat, type='INCOME',
                                    amount=Decimal('1000.00'), date='2026-06-05')
        Transaction.objects.create(user=self.user, category=self.expense_cat, type='EXPENSE',
                                    amount=Decimal('300.00'), date='2026-06-05')
        # different month - should not count
        Transaction.objects.create(user=self.user, category=self.expense_cat, type='EXPENSE',
                                    amount=Decimal('999.00'), date='2026-05-05')

    def test_monthly_totals(self):
        resp = self.client.get('/api/analytics/monthly/?year=2026&month=6')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(Decimal(str(data['total_income'])), Decimal('1000.00'))
        self.assertEqual(Decimal(str(data['total_expense'])), Decimal('300.00'))
        self.assertEqual(Decimal(str(data['net'])), Decimal('700.00'))

    def test_requires_authentication(self):
        self.client.force_authenticate(None)
        resp = self.client.get('/api/analytics/monthly/')
        self.assertEqual(resp.status_code, 401)
