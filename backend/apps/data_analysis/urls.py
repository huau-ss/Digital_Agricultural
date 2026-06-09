from django.urls import path
from .views import (
    PricePredictionView, ProductListForPredictionView, ModelInfoView, MarketListView
)
from .warning_views import TriggerWarningCheckView, CheckProductWarningView, ListProductsForWarningView
from .dashboard_views import DashboardSummaryView, RecentWarningsView
from .admin_settings_views import AdminSettingsView
from .model_registry_views import ModelRegistryView, ModelDetailView

app_name = 'data_analysis'

urlpatterns = [
    # 价格预测
    path('prediction/', PricePredictionView.as_view(), name='prediction'),
    path('prediction/products/', ProductListForPredictionView.as_view(), name='prediction-products'),
    path('prediction/markets/', MarketListView.as_view(), name='prediction-markets'),
    path('prediction/model-info/', ModelInfoView.as_view(), name='model-info'),
    # 价格预警
    path('warning/check/', TriggerWarningCheckView.as_view(), name='warning-check'),
    path('warning/check-product/', CheckProductWarningView.as_view(), name='warning-check-product'),
    path('warning/products/', ListProductsForWarningView.as_view(), name='warning-products'),
    # Dashboard 仪表盘
    path('dashboard/summary/', DashboardSummaryView.as_view(), name='dashboard-summary'),
    # 今日预警
    path('warning/recent/', RecentWarningsView.as_view(), name='recent-warnings'),
    # 管理员系统设置
    path('admin/settings/', AdminSettingsView.as_view(), name='admin-settings'),
    # 模型管理
    path('admin/models/', ModelRegistryView.as_view(), name='model-registry'),
    path('admin/models/<int:product_id>/', ModelDetailView.as_view(), name='model-detail'),
]
