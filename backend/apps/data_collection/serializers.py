from rest_framework import serializers
from .models import AgriculturalProduct, PriceHistory, CleanedPriceData


class AgriculturalProductSerializer(serializers.ModelSerializer):
    """农产品序列化器"""
    category_display = serializers.CharField(source='get_category_display', read_only=True)

    class Meta:
        model = AgriculturalProduct
        fields = ['id', 'name', 'category', 'category_display', 'origin', 'unit',
                  'description', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class PriceHistorySerializer(serializers.ModelSerializer):
    """历史价格序列化器"""
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_category = serializers.CharField(source='product.category', read_only=True)

    class Meta:
        model = PriceHistory
        fields = ['id', 'product', 'product_name', 'product_category', 'market_name',
                  'date', 'avg_price', 'max_price', 'min_price', 'volume', 'source',
                  'remarks', 'created_at']
        read_only_fields = ['id', 'created_at']


class CleanedPriceDataSerializer(serializers.ModelSerializer):
    """清洗后价格数据序列化器"""
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_category = serializers.CharField(source='product.category', read_only=True)

    class Meta:
        model = CleanedPriceData
        fields = ['id', 'product', 'product_name', 'product_category', 'market_name',
                  'date', 'avg_price', 'max_price', 'min_price', 'volume', 'source',
                  'is_outlier', 'outlier_reason', 'created_at']
        read_only_fields = ['id', 'created_at']


class PriceHistoryQuerySerializer(serializers.Serializer):
    """价格历史查询参数序列化器"""
    product_id = serializers.IntegerField(required=False, label='产品ID')
    market_name = serializers.CharField(required=False, label='市场名称')
    start_date = serializers.DateField(required=False, label='开始日期')
    end_date = serializers.DateField(required=False, label='结束日期')
