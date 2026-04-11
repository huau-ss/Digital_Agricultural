from django.contrib import admin
from .models import AgriculturalProduct, PriceHistory, CleanedPriceData


@admin.register(AgriculturalProduct)
class AgriculturalProductAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'category', 'origin', 'unit', 'is_active', 'created_at']
    search_fields = ['name', 'category', 'origin']
    list_filter = ['category', 'is_active']
    list_editable = ['is_active']


@admin.register(PriceHistory)
class PriceHistoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'product', 'market_name', 'date', 'avg_price', 'max_price', 'min_price', 'volume', 'created_at']
    search_fields = ['product__name', 'market_name']
    list_filter = ['date', 'market_name', 'product__category']
    date_hierarchy = 'date'
    readonly_fields = ['created_at']


@admin.register(CleanedPriceData)
class CleanedPriceDataAdmin(admin.ModelAdmin):
    list_display = ['id', 'product', 'market_name', 'date', 'avg_price', 'is_outlier', 'outlier_reason', 'created_at']
    search_fields = ['product__name', 'market_name']
    list_filter = ['date', 'market_name', 'is_outlier', 'product__category']
    date_hierarchy = 'date'
    readonly_fields = ['created_at']
