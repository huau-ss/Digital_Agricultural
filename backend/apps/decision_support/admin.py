from django.contrib import admin
from .models import TradeInfo


@admin.register(TradeInfo)
class TradeInfoAdmin(admin.ModelAdmin):
    list_display = ['id', 'publisher', 'info_type', 'product', 'quantity', 'expected_price', 'status', 'created_at']
    list_filter = ['info_type', 'status', 'created_at']
    search_fields = ['publisher__username', 'product__name', 'origin']
    date_hierarchy = 'created_at'
