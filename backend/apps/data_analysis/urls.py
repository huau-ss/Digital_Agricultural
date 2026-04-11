from django.urls import path
from .views import (
    PricePredictionView, ProductListForPredictionView, ModelInfoView
)
from .warning_views import TriggerWarningCheckView, CheckProductWarningView, ListProductsForWarningView
from .dashboard_views import DashboardSummaryView

app_name = 'data_analysis'

urlpatterns = [
    # 价格预测
    path('prediction/', PricePredictionView.as_view(), name='prediction'),
    path('prediction/products/', ProductListForPredictionView.as_view(), name='prediction-products'),
    path('prediction/model-info/', ModelInfoView.as_view(), name='model-info'),
    # 价格预警
    path('warning/check/', TriggerWarningCheckView.as_view(), name='warning-check'),
    path('warning/check-product/', CheckProductWarningView.as_view(), name='warning-check-product'),
    path('warning/products/', ListProductsForWarningView.as_view(), name='warning-products'),
    # Dashboard 仪表盘
    path('dashboard/summary/', DashboardSummaryView.as_view(), name='dashboard-summary'),
]
