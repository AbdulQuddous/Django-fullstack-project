from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import BudgetAlertsView, BudgetViewSet

router = DefaultRouter()
router.register('', BudgetViewSet, basename='budget')

urlpatterns = [
    path('alerts/', BudgetAlertsView.as_view(), name='budget-alerts'),
] + router.urls
