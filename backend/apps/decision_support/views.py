from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db import transaction

from .models import TradeInfo, Order, OrderStatusLog
from .serializers import TradeInfoSerializer, OrderSerializer, OrderCreateSerializer, OrderAcceptSerializer


class TradeInfoViewSet(viewsets.ModelViewSet):
    """供需信息视图集"""
    serializer_class = TradeInfoSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['info_type', 'status', 'product', 'publisher']

    def get_queryset(self):
        return TradeInfo.objects.select_related('publisher', 'product').all()

    @action(detail=False, methods=['get'])
    def my_posts(self, request):
        """获取当前用户发布的信息"""
        queryset = self.get_queryset().filter(publisher=request.user)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """标记为已成交"""
        trade_info = self.get_object()
        if trade_info.publisher != request.user:
            return Response({'error': '无权限操作'}, status=status.HTTP_403_FORBIDDEN)
        trade_info.status = 'completed'
        trade_info.save()
        return Response({'message': '已标记为成交'})

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """取消信息"""
        trade_info = self.get_object()
        if trade_info.publisher != request.user:
            return Response({'error': '无权限操作'}, status=status.HTTP_403_FORBIDDEN)
        trade_info.status = 'cancelled'
        trade_info.save()
        return Response({'message': '已取消'})


class OrderViewSet(viewsets.ModelViewSet):
    """订单视图集"""
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'product']

    def get_queryset(self):
        queryset = Order.objects.select_related('buyer', 'seller', 'product', 'trade_info').all()
        role = getattr(self.request.user, 'role', None)

        if role == 'buyer':
            queryset = queryset.filter(buyer=self.request.user)
        elif role == 'farmer':
            queryset = queryset.filter(seller=self.request.user)
        else:
            queryset = queryset.filter(buyer=self.request.user) | queryset.filter(seller=self.request.user)

        return queryset.distinct().order_by('-created_at')

    def get_serializer_class(self):
        if self.action == 'create':
            return OrderCreateSerializer
        if self.action == 'accept_order':
            return OrderAcceptSerializer
        return OrderSerializer

    @action(detail=False, methods=['get'])
    def my_orders(self, request):
        """获取当前用户的订单"""
        queryset = self.get_queryset()
        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def accept_order(self, request):
        """
        接受订单（农户接受采购商的需求订单）
        此时：农户为卖方，采购商为买方
        """
        from .serializers import OrderAcceptSerializer
        serializer = OrderAcceptSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        trade_info = serializer.validated_data['trade_info']
        user = request.user

        # 农户只能接受采购商发布的求购信息，不能接受自己发布的
        if trade_info.publisher == user:
            return Response({'error': '不能接受自己发布的订单'}, status=status.HTTP_400_BAD_REQUEST)
        if trade_info.info_type != 'demand':
            return Response({'error': '只能接受求购信息'}, status=status.HTTP_400_BAD_REQUEST)
        if trade_info.status != 'active':
            return Response({'error': '该供需信息已结束'}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            order = Order.objects.create(
                buyer=trade_info.publisher,  # 采购商是买方
                seller=user,  # 农户是卖方
                trade_info=trade_info,
                product=serializer.validated_data['product'],
                quantity=serializer.validated_data['quantity'],
                unit=serializer.validated_data.get('unit', '斤'),
                unit_price=serializer.validated_data.get('unit_price', 0),
                buyer_contact=serializer.validated_data.get('buyer_contact', ''),
                delivery_address=serializer.validated_data.get('delivery_address', ''),
                remark=serializer.validated_data.get('remark', '')
            )

            trade_info.status = 'completed'
            trade_info.save()

            OrderStatusLog.objects.create(
                order=order,
                to_status='pending',
                operator=user,
                remark='接受订单'
            )

        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        """确认订单（卖方）"""
        order = self.get_object()
        if order.seller != request.user:
            return Response({'error': '无权限操作'}, status=status.HTTP_403_FORBIDDEN)
        if order.status != 'pending':
            return Response({'error': '订单状态不允许确认'}, status=status.HTTP_400_BAD_REQUEST)

        old_status = order.status
        order.status = 'confirmed'
        order.save()

        OrderStatusLog.objects.create(
            order=order, from_status=old_status, to_status='confirmed',
            operator=request.user, remark='确认订单'
        )
        return Response({'message': '订单已确认'})

    @action(detail=True, methods=['post'])
    def ship(self, request, pk=None):
        """发货（卖方）"""
        order = self.get_object()
        if order.seller != request.user:
            return Response({'error': '无权限操作'}, status=status.HTTP_403_FORBIDDEN)
        if order.status != 'confirmed':
            return Response({'error': '订单状态不允许发货'}, status=status.HTTP_400_BAD_REQUEST)

        old_status = order.status
        order.status = 'shipped'
        order.save()

        OrderStatusLog.objects.create(
            order=order, from_status=old_status, to_status='shipped',
            operator=request.user, remark='已发货'
        )
        return Response({'message': '已发货'})

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """完成订单（买方）"""
        order = self.get_object()
        if order.buyer != request.user:
            return Response({'error': '无权限操作'}, status=status.HTTP_403_FORBIDDEN)
        if order.status != 'shipped':
            return Response({'error': '订单状态不允许完成'}, status=status.HTTP_400_BAD_REQUEST)

        old_status = order.status
        order.status = 'completed'
        order.save()

        OrderStatusLog.objects.create(
            order=order, from_status=old_status, to_status='completed',
            operator=request.user, remark='确认收货'
        )
        return Response({'message': '订单已完成'})

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """取消订单"""
        order = self.get_object()
        if order.buyer != request.user and order.seller != request.user:
            return Response({'error': '无权限操作'}, status=status.HTTP_403_FORBIDDEN)
        if order.status in ['completed', 'cancelled']:
            return Response({'error': '订单状态不允许取消'}, status=status.HTTP_400_BAD_REQUEST)

        old_status = order.status
        order.status = 'cancelled'
        order.save()

        if order.trade_info:
            order.trade_info.status = 'active'
            order.trade_info.save()

        OrderStatusLog.objects.create(
            order=order, from_status=old_status, to_status='cancelled',
            operator=request.user, remark='取消订单'
        )
        return Response({'message': '订单已取消'})
