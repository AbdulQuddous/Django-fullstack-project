from rest_framework import serializers

from .models import Budget


class BudgetSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Budget
        fields = ['id', 'category', 'category_name', 'monthly_limit', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_category(self, category):
        request = self.context['request']
        if category.user_id is not None and category.user_id != request.user.id:
            raise serializers.ValidationError("You don't have access to this category.")
        if category.type != category.EXPENSE:
            raise serializers.ValidationError('Budgets can only be set on expense categories.')
        return category
