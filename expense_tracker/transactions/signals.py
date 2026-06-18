from django.core.mail import send_mail
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.dateparse import parse_date

from .models import Transaction


@receiver(post_save, sender=Transaction)
def check_budget_on_transaction_save(sender, instance, created, **kwargs):
    """
    After an expense transaction is saved, check whether it pushed the
    relevant category's monthly budget to >=80% (warning) or >=100%
    (exceeded), and email the user if so (console backend by default).
    """
    if instance.type != Transaction.EXPENSE:
        return

    from budgets.models import Budget
    from budgets.utils import get_budget_status

    budget = Budget.objects.filter(user=instance.user, category=instance.category).first()
    if not budget:
        return

    # instance.date is normally already a `date` object (DRF's serializer
    # parses incoming strings before save), but if a Transaction is ever
    # created directly via the ORM with a raw string, coerce it here too.
    tx_date = instance.date
    if isinstance(tx_date, str):
        tx_date = parse_date(tx_date)
    if tx_date is None:
        return

    status = get_budget_status(budget, year=tx_date.year, month=tx_date.month)
    if status['status'] in ('WARNING', 'EXCEEDED'):
        subject = (
            f"Budget {status['status'].lower()}: {instance.category.name}"
        )
        message = (
            f"Heads up - your '{instance.category.name}' spending is now "
            f"{status['percent_used']}% of your {status['monthly_limit']} monthly budget "
            f"(spent {status['spent']})."
        )
        send_mail(
            subject,
            message,
            None,
            [instance.user.email or 'no-reply@example.com'],
            fail_silently=True,
        )
