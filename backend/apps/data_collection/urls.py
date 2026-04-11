from rest_framework.routers import DefaultRouter
from .views import AgriculturalProductViewSet, PriceHistoryViewSet, CleanedPriceDataViewSet
from .views_visualization import VisualizationViewSet

router = DefaultRouter()
router.register(r'products', AgriculturalProductViewSet, basename='product')
router.register(r'price-history', PriceHistoryViewSet, basename='price-history')
router.register(r'cleaned-prices', CleanedPriceDataViewSet, basename='cleaned-price')
router.register(r'visualization', VisualizationViewSet, basename='visualization')

urlpatterns = router.urls
