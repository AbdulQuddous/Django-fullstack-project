from decimal import Decimal

from django.db.models import Sum
from django.utils import timezone


def get_budget_status(budget, year=None, month=None):
    """
    Compute how much of `budget` has been spent in the given month
    (defaults to the current month) and flag WARNING at >=80% used,
    EXCEEDED at >=100% used.
    """
    # Imported here (not at module level) to avoid a circular import,
    # since transactions/signals.py imports this module.
    from transactions.models import Transaction

    today = timezone.localdate()
    year = year or today.year
    month = month or today.month

    spent = Transaction.objects.filter(
        user=budget.user,
        category=budget.category,
        type=Transaction.EXPENSE,
        date__year=year,
        date__month=month,
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    limit = budget.monthly_limit
    percent_used = float(spent / limit * 100) if limit else 0.0

    if percent_used >= 100:
        status = 'EXCEEDED'
    elif percent_used >= 80:
        status = 'WARNING'
    else:
        status = 'OK'

    return {
        'budget_id': budget.id,
        'category': budget.category.name,
        'category_id': budget.category_id,
        'year': year,
        'month': month,
        'monthly_limit': limit,
        'spent': spent,
        'percent_used': round(percent_used, 2),
        'status': status,
    }
