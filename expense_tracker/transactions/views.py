import csv

from django.http import HttpResponse
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from .models import Transaction
from .serializers import TransactionSerializer


class TransactionViewSet(viewsets.ModelViewSet):
    """
    CRUD for income/expense transactions, scoped to the authenticated user.

    Supports filtering via query params, e.g.:
        /api/transactions/?type=EXPENSE&category=3
        /api/transactions/?date__gte=2026-06-01&date__lte=2026-06-30
        /api/transactions/?search=coffee
        /api/transactions/?ordering=-amount
    """
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = {
        'category': ['exact'],
        'type': ['exact'],
        'date': ['exact', 'gte', 'lte'],
    }
    search_fields = ['description']
    ordering_fields = ['date', 'amount', 'created_at']

    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user).select_related('category')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'])
    def export(self, request):
        """CSV export of the (optionally filtered) transaction list: /api/transactions/export/"""
        queryset = self.filter_queryset(self.get_queryset())

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="transactions.csv"'

        writer = csv.writer(response)
        writer.writerow(['Date', 'Type', 'Category', 'Amount', 'Description'])
        for tx in queryset:
            writer.writerow([tx.date, tx.type, tx.category.name, tx.amount, tx.description])

        return response
