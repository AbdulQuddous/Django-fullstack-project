from django.urls import path

from .views import MonthlyAnalyticsView, TrendsAnalyticsView

urlpatterns = [
    path('monthly/', MonthlyAnalyticsView.as_view(), name='analytics-monthly'),
    path('trends/', TrendsAnalyticsView.as_view(), name='analytics-trends'),
]
