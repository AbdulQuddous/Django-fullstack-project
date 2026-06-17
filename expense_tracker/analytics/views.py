from django.shortcuts import render

# Create your views here.
from dateutil.relativedelta import relativedelta
from django.db.models import Q, Sum
from django.db.models.functions import TruncMonth
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from budgets.models import Budget
from budgets.utils import get_budget_status
from transactions.models import Transaction


class MonthlyAnalyticsView(APIView):
    """
    GET /api/analytics/monthly/?year=&month=

    Spending/income for one month, broken down by category, with budget
    status (OK/WARNING/EXCEEDED) attached to any expense category that
    has a budget set.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        today = timezone.localdate()
        year = int(request.query_params.get('year', today.year))
        month = int(request.query_params.get('month', today.month))

        qs = Transaction.objects.filter(user=request.user, date__year=year, date__month=month)

        totals = qs.aggregate(
            total_income=Sum('amount', filter=Q(type=Transaction.INCOME)),
            total_expense=Sum('amount', filter=Q(type=Transaction.EXPENSE)),
        )
        total_income = totals['total_income'] or 0
        total_expense = totals['total_expense'] or 0

        by_category = list(
            qs.values('category_id', 'category__name', 'type')
            .annotate(total=Sum('amount'))
            .order_by('type', '-total')
        )

        budgets_by_category = {
            b.category_id: b for b in Budget.objects.filter(user=request.user)
        }
        for row in by_category:
            row['category'] = row.pop('category__name')
            budget = budgets_by_category.get(row['category_id'])
            if budget:
                status = get_budget_status(budget, year=year, month=month)
                row['budget_limit'] = status['monthly_limit']
                row['percent_used'] = status['percent_used']
                row['budget_status'] = status['status']
            else:
                row['budget_limit'] = None
                row['percent_used'] = None
                row['budget_status'] = None

        return Response({
            'year': year,
            'month': month,
            'total_income': total_income,
            'total_expense': total_expense,
            'net': total_income - total_expense,
            'by_category': by_category,
        })


class TrendsAnalyticsView(APIView):
    """
    GET /api/analytics/trends/?months=6

    Income vs. expense totals for each of the last N months (default 6),
    oldest first - handy for a "spending over time" chart on a frontend.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        months = int(request.query_params.get('months', 6))
        today = timezone.localdate()
        start = (today.replace(day=1) - relativedelta(months=months - 1))

        qs = (
            Transaction.objects.filter(user=request.user, date__gte=start)
            .annotate(month=TruncMonth('date'))
            .values('month', 'type')
            .annotate(total=Sum('amount'))
            .order_by('month')
        )

        buckets = {}
        cursor = start
        for _ in range(months):
            key = cursor.strftime('%Y-%m')
            buckets[key] = {'month': key, 'income': 0, 'expense': 0}
            cursor += relativedelta(months=1)

        for row in qs:
            key = row['month'].strftime('%Y-%m')
            if key not in buckets:
                continue
            if row['type'] == Transaction.INCOME:
                buckets[key]['income'] = row['total']
            else:
                buckets[key]['expense'] = row['total']

        results = list(buckets.values())
        for r in results:
            r['net'] = r['income'] - r['expense']

        return Response(results)
