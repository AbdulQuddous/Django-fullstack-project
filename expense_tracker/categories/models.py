from django.conf import settings
from django.db import models


class Category(models.Model):

    INCOME = 'INCOME'
    EXPENSE = 'EXPENSE'
    TYPE_CHOICES = [
        (INCOME, 'Income'),
        (EXPENSE, 'Expense'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='categories',
        null=True,
        blank=True,
        help_text='Null for global default categories available to everyone.',
    )
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=7, choices=TYPE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['type', 'name']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'name', 'type'],
                name='unique_category_per_user',
            )
        ]

    def __str__(self):
        owner = self.user.username if self.user_id else 'default'
        return f"{self.name} ({self.get_type_display()}) [{owner}]"
