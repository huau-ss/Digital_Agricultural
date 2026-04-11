from rest_framework import serializers
from .models import TradeInfo


class TradeInfoSerializer(serializers.ModelSerializer):
    """供需信息序列化器"""
    publisher_name = serializers.CharField(source='publisher.username', read_only=True)
    publisher_role = serializers.CharField(source='publisher.role', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    info_type_display = serializers.CharField(source='get_info_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = TradeInfo
        fields = [
            'id', 'publisher', 'publisher_name', 'publisher_role',
            'info_type', 'info_type_display', 'product', 'product_name',
            'quantity', 'unit', 'expected_price', 'origin', 'contact_phone',
            'description', 'status', 'status_display', 'created_at', 'updated_at'
        ]
        read_only_fields = ['publisher', 'created_at', 'updated_at']

    def validate(self, data):
        # 农户只能发布供应，采购商只能发布求购
        user = self.context['request'].user
        info_type = data.get('info_type')

        if user.role == 'farmer' and info_type == 'demand':
            raise serializers.ValidationError({'info_type': '农户只能发布供应信息'})
        if user.role == 'buyer' and info_type == 'supply':
            raise serializers.ValidationError({'info_type': '采购商只能发布求购信息'})

        return data

    def create(self, validated_data):
        validated_data['publisher'] = self.context['request'].user
        return super().create(validated_data)
