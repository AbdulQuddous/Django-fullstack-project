from django.db.models import Q
from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied

from .models import Category
from .serializers import CategorySerializer


class CategoryViewSet(viewsets.ModelViewSet):
    """
    CRUD for categories. Each user sees the global default categories
    plus any categories they created themselves. Default categories
    cannot be edited or deleted through the API.
    """
    serializer_class = CategorySerializer
    filterset_fields = ['type']
    search_fields = ['name']
    ordering_fields = ['name', 'created_at']

    def get_queryset(self):
        user = self.request.user
        return Category.objects.filter(Q(user=user) | Q(user__isnull=True))

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        if serializer.instance.user_id is None:
            raise PermissionDenied('Default categories cannot be modified.')
        serializer.save()

    def perform_destroy(self, instance):
        if instance.user_id is None:
            raise PermissionDenied('Default categories cannot be deleted.')
        instance.delete()
