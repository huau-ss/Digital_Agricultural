from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TradeInfoViewSet

router = DefaultRouter()
router.register(r'trade-info', TradeInfoViewSet, basename='trade-info')

app_name = 'decision_support'

urlpatterns = [
    path('', include(router.urls)),
]
