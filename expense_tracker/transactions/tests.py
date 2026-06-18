from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from categories.models import Category
from transactions.models import Transaction

User = get_user_model()


class TransactionTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='alice', password='pass12345!')
        self.client.force_authenticate(self.user)
        self.expense_cat = Category.objects.create(user=self.user, name='Groceries', type=Category.EXPENSE)
        self.income_cat = Category.objects.create(user=self.user, name='Salary', type=Category.INCOME)

    def test_create_transaction(self):
        resp = self.client.post('/api/transactions/', {
            'category': self.expense_cat.id, 'type': 'EXPENSE',
            'amount': '50.00', 'date': '2026-06-01',
        })
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(Transaction.objects.count(), 1)

    def test_category_type_mismatch_rejected(self):
        resp = self.client.post('/api/transactions/', {
            'category': self.income_cat.id, 'type': 'EXPENSE',
            'amount': '50.00', 'date': '2026-06-01',
        })
        self.assertEqual(resp.status_code, 400)

    def test_cannot_use_other_users_category(self):
        other = User.objects.create_user(username='mallory', password='pass12345!')
        other_cat = Category.objects.create(user=other, name='Secret', type=Category.EXPENSE)
        resp = self.client.post('/api/transactions/', {
            'category': other_cat.id, 'type': 'EXPENSE',
            'amount': '50.00', 'date': '2026-06-01',
        })
        self.assertEqual(resp.status_code, 400)

    def test_transactions_scoped_to_user(self):
        other = User.objects.create_user(username='mallory', password='pass12345!')
        other_cat = Category.objects.create(user=other, name='Other', type=Category.EXPENSE)
        Transaction.objects.create(user=other, category=other_cat, type='EXPENSE',
                                    amount=Decimal('10.00'), date='2026-06-01')
        Transaction.objects.create(user=self.user, category=self.expense_cat, type='EXPENSE',
                                    amount=Decimal('20.00'), date='2026-06-01')
        resp = self.client.get('/api/transactions/')
        self.assertEqual(resp.json()['count'], 1)

    def test_csv_export(self):
        Transaction.objects.create(user=self.user, category=self.expense_cat, type='EXPENSE',
                                    amount=Decimal('20.00'), date='2026-06-01')
        resp = self.client.get('/api/transactions/export/')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('text/csv', resp['Content-Type'])
