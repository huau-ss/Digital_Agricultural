from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AgriculturalProductViewSet, PriceHistoryViewSet, CleanedPriceDataViewSet, TriggerDataCollectionView, TriggerDataCleaningView
from .views_visualization import VisualizationViewSet

# 注册视图集，自动生成多个 URL
router = DefaultRouter()
router.register(r'products', AgriculturalProductViewSet, basename='product')
router.register(r'price-history', PriceHistoryViewSet, basename='price-history')
router.register(r'cleaned-prices', CleanedPriceDataViewSet, basename='cleaned-price')
router.register(r'visualization', VisualizationViewSet, basename='visualization')

urlpatterns = router.urls

urlpatterns += [
    path('trigger/collect/', TriggerDataCollectionView.as_view(), name='trigger-collect'),
    path('trigger/clean/', TriggerDataCleaningView.as_view(), name='trigger-clean'),
]
