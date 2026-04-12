from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TradeInfoViewSet, OrderViewSet

router = DefaultRouter()
router.register(r'trade-info', TradeInfoViewSet, basename='trade-info')
router.register(r'orders', OrderViewSet, basename='orders')

app_name = 'decision_support'

urlpatterns = [
    path('', include(router.urls)),
]
