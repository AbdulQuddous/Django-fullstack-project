from rest_framework import serializers

from .models import Transaction


class TransactionSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Transaction
        fields = [
            'id', 'category', 'category_name', 'type', 'amount',
            'description', 'date', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate(self, attrs):
        category = attrs.get('category') or getattr(self.instance, 'category', None)
        tx_type = attrs.get('type') or getattr(self.instance, 'type', None)

        request = self.context['request']
        if category and category.user_id is not None and category.user_id != request.user.id:
            raise serializers.ValidationError(
                {'category': "You don't have access to this category."}
            )

        if category and tx_type and category.type != tx_type:
            raise serializers.ValidationError(
                {'type': f"Category '{category.name}' is a {category.get_type_display()} "
                          f"category and can't be used for a {tx_type.lower()} transaction."}
            )
        return attrs
