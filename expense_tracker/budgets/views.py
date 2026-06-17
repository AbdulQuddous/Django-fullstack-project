from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Budget
from .serializers import BudgetSerializer
from .utils import get_budget_status


class BudgetViewSet(viewsets.ModelViewSet):
    """CRUD for the authenticated user's per-category monthly budgets."""
    serializer_class = BudgetSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Budget.objects.filter(user=self.request.user).select_related('category')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class BudgetAlertsView(APIView):
    """
    GET /api/budgets/alerts/?year=&month=&only_alerts=true

    Returns the status (OK / WARNING / EXCEEDED) of every budget the user
    has set for the given month (defaults to the current month).
    Pass only_alerts=true to return just the WARNING/EXCEEDED ones.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        year = request.query_params.get('year')
        month = request.query_params.get('month')
        only_alerts = request.query_params.get('only_alerts', 'false').lower() == 'true'

        year = int(year) if year else None
        month = int(month) if month else None

        budgets = Budget.objects.filter(user=request.user).select_related('category')
        results = [get_budget_status(b, year=year, month=month) for b in budgets]

        if only_alerts:
            results = [r for r in results if r['status'] != 'OK']

        return Response(results)
