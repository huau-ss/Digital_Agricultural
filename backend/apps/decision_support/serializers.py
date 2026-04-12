from rest_framework import serializers
from .models import TradeInfo, Order, OrderStatusLog
from apps.data_collection.models import AgriculturalProduct


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
        if self.instance:
            return data

        user = self.context.get('request', {}).user
        if not user or not user.is_authenticated:
            return data

        info_type = data.get('info_type')
        if hasattr(user, 'role'):
            if user.role == 'farmer' and info_type == 'demand':
                raise serializers.ValidationError({'info_type': '农户只能发布供应信息'})
            if user.role == 'buyer' and info_type == 'supply':
                raise serializers.ValidationError({'info_type': '采购商只能发布求购信息'})

        return data

    def create(self, validated_data):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['publisher'] = request.user
        return super().create(validated_data)


class OrderSerializer(serializers.ModelSerializer):
    """订单序列化器"""
    buyer_id = serializers.IntegerField(source='buyer.id', read_only=True, allow_null=True)
    seller_id = serializers.IntegerField(source='seller.id', read_only=True, allow_null=True)
    buyer_name = serializers.CharField(source='buyer.username', read_only=True, allow_null=True)
    seller_name = serializers.CharField(source='seller.username', read_only=True, allow_null=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    trade_info_id = serializers.IntegerField(source='trade_info.id', read_only=True, allow_null=True)

    class Meta:
        model = Order
        fields = [
            'id', 'order_no',
            'buyer', 'buyer_id', 'buyer_name',
            'seller', 'seller_id', 'seller_name',
            'trade_info', 'trade_info_id',
            'product', 'product_name', 'quantity', 'unit', 'unit_price', 'total_amount',
            'status', 'status_display',
            'buyer_contact', 'seller_contact', 'delivery_address', 'remark',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['order_no', 'buyer', 'seller', 'total_amount', 'created_at', 'updated_at']


class OrderCreateSerializer(serializers.ModelSerializer):
    """创建订单序列化器"""

    class Meta:
        model = Order
        fields = [
            'trade_info', 'product', 'quantity', 'unit', 'unit_price',
            'buyer_contact', 'delivery_address', 'remark'
        ]

    def validate(self, data):
        request = self.context.get('request')
        if not request or not request.user:
            raise serializers.ValidationError('需要登录才能创建订单')

        trade_info = data.get('trade_info')
        if trade_info:
            if trade_info.publisher == request.user:
                raise serializers.ValidationError('不能购买自己发布的商品')
            if trade_info.status != 'active':
                raise serializers.ValidationError('该供需信息已结束')

        return data

    def create(self, validated_data):
        request = self.context.get('request')
        user = request.user

        trade_info = validated_data.pop('trade_info', None)

        order = Order(
            buyer=user,
            seller=trade_info.publisher if trade_info else None,
            trade_info=trade_info,
            buyer_contact=validated_data.get('buyer_contact', user.phone or ''),
            unit='斤'
        )

        for field in ['product', 'quantity', 'unit_price']:
            if field in validated_data:
                setattr(order, field, validated_data[field])

        order.save()

        if trade_info:
            trade_info.status = 'completed'
            trade_info.save()

        OrderStatusLog.objects.create(
            order=order,
            to_status='pending',
            operator=user,
            remark='创建订单'
        )

        return order


class OrderAcceptSerializer(serializers.Serializer):
    """接受订单序列化器"""
    trade_info = serializers.PrimaryKeyRelatedField(queryset=TradeInfo.objects.all())
    product = serializers.PrimaryKeyRelatedField(queryset=AgriculturalProduct.objects.all(), required=False)
    quantity = serializers.DecimalField(max_digits=10, decimal_places=2)
    unit = serializers.CharField(max_length=20, default='斤')
    unit_price = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    buyer_contact = serializers.CharField(max_length=20, required=False, allow_blank=True)
    delivery_address = serializers.CharField(max_length=200, required=False, allow_blank=True)
    remark = serializers.CharField(required=False, allow_blank=True)
