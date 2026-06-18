from django.db import migrations

DEFAULT_INCOME_CATEGORIES = ['Salary', 'Freelance', 'Investments', 'Other Income']
DEFAULT_EXPENSE_CATEGORIES = [
    'Groceries', 'Rent', 'Utilities', 'Transport', 'Dining Out',
    'Entertainment', 'Healthcare', 'Shopping', 'Other Expense',
]


def seed_categories(apps, schema_editor):
    Category = apps.get_model('categories', 'Category')
    for name in DEFAULT_INCOME_CATEGORIES:
        Category.objects.get_or_create(user=None, name=name, type='INCOME')
    for name in DEFAULT_EXPENSE_CATEGORIES:
        Category.objects.get_or_create(user=None, name=name, type='EXPENSE')


def remove_categories(apps, schema_editor):
    Category = apps.get_model('categories', 'Category')
    Category.objects.filter(user=None).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('categories', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_categories, remove_categories),
    ]
