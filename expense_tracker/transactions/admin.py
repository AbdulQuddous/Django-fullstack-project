from django.contrib import admin

from .models import Transaction


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['date', 'user', 'type', 'category', 'amount']
    list_filter = ['type', 'date']
    search_fields = ['description', 'user__username']
