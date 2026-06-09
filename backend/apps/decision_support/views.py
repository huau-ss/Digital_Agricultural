# REST Framework 相关导入
# viewsets.ModelViewSet: 提供完整的 CRUD 功能（list/retrieve/create/update/destroy）
# status: HTTP 状态码常量，如 status.HTTP_403_FORBIDDEN
# permissions: 权限控制类，如 IsAuthenticated 要求登录
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db import transaction

# 导入本 app 的模型和序列化器
from .models import TradeInfo, Order, OrderStatusLog
from .serializers import TradeInfoSerializer, OrderSerializer, OrderCreateSerializer, OrderAcceptSerializer


# =============================================================================
# TradeInfoViewSet - 供需信息视图集
# 提供供需信息的 CRUD 功能（增删改查）
# =============================================================================
class TradeInfoViewSet(viewsets.ModelViewSet):
    """
    供需信息视图集

    提供接口：
    - GET    /trade-info/          - 列出所有供需信息（支持过滤、分页）
    - POST   /trade-info/          - 创建供需信息
    - GET    /trade-info/{id}/     - 获取单个供需信息详情
    - PUT    /trade-info/{id}/     - 更新供需信息
    - DELETE /trade-info/{id}/     - 删除供需信息
    - GET    /trade-info/my_posts/ - 获取当前用户发布的供需信息
    - POST   /trade-info/{id}/complete/ - 标记为已成交
    - POST   /trade-info/{id}/cancel/   - 取消供需信息
    """

    # 指定序列化器：列表/详情时使用 TradeInfoSerializer
    serializer_class = TradeInfoSerializer

    # 权限控制：只有登录用户才能访问
    permission_classes = [permissions.IsAuthenticated]

    # 启用字段过滤后端
    filter_backends = [DjangoFilterBackend]

    # 支持过滤的字段：info_type(供应/求购), status(状态), product(农产品), publisher(发布者)
    # 使用示例：GET /trade-info/?info_type=supply&status=active
    filterset_fields = ['info_type', 'status', 'product', 'publisher']

    def get_queryset(self):
        """
        获取供需信息查询集

        select_related() 预加载关联表，避免 N+1 查询问题：
        - publisher: 发布者用户信息
        - product: 关联的农产品信息

        Returns:
            QuerySet: 包含用户和农产品关联数据的查询集
        """
        return TradeInfo.objects.select_related('publisher', 'product').all()

    @action(detail=False, methods=['get'])
    def my_posts(self, request):
        """
        获取当前用户发布的所有供需信息

        URL: GET /trade-info/my_posts/
        Returns: 分页的供需信息列表

        逻辑：根据 request.user 过滤，只返回当前用户发布的记录
        """
        # 过滤：只返回发布者等于当前用户的记录
        queryset = self.get_queryset().filter(publisher=request.user)

        # 启用分页
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        # 不需要分页时直接返回
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """
        将供需信息标记为已成交

        URL: POST /trade-info/{id}/complete/
        权限：只有发布者才能操作
        """
        trade_info = self.get_object()  # 获取 URL 中的 {pk} 对应的记录

        # 权限检查：只有发布者本人才能标记为成交
        if trade_info.publisher != request.user:
            return Response({'error': '无权限操作'}, status=status.HTTP_403_FORBIDDEN)

        # 更新状态
        trade_info.status = 'completed'
        trade_info.save()

        return Response({'message': '已标记为成交'})

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        取消供需信息

        URL: POST /trade-info/{id}/cancel/
        权限：只有发布者才能操作
        """
        trade_info = self.get_object()

        # 权限检查
        if trade_info.publisher != request.user:
            return Response({'error': '无权限操作'}, status=status.HTTP_403_FORBIDDEN)

        # 更新状态
        trade_info.status = 'cancelled'
        trade_info.save()

        return Response({'message': '已取消'})


# =============================================================================
# OrderViewSet - 订单视图集
# 提供订单的 CRUD 功能和状态流转操作
# =============================================================================
class OrderViewSet(viewsets.ModelViewSet):
    """
    订单视图集

    提供接口：
    - GET    /orders/              - 列出当前用户的订单（按角色过滤）
    - POST   /orders/             - 创建订单
    - GET    /orders/{id}/        - 获取订单详情
    - PUT    /orders/{id}/        - 更新订单
    - DELETE /orders/{id}/        - 删除订单
    - GET    /orders/my_orders/   - 获取当前用户的订单（支持状态过滤）
    - POST   /orders/accept_order/           - 农户接受采购商的求购订单
    - POST   /orders/{id}/confirm/           - 卖方确认订单
    - POST   /orders/{id}/ship/              - 卖方发货
    - POST   /orders/{id}/complete/          - 买方确认收货
    - POST   /orders/{id}/cancel/            - 取消订单
    """

    # 默认序列化器
    serializer_class = OrderSerializer

    # 权限控制：需要登录
    permission_classes = [permissions.IsAuthenticated]

    # 启用字段过滤
    filter_backends = [DjangoFilterBackend]

    # 支持过滤的字段：status(订单状态), product(农产品)
    filterset_fields = ['status', 'product']

    def get_queryset(self):
        """
        获取订单查询集（根据用户角色过滤）

        角色权限：
        - buyer（采购商）：只能看到自己作为买方的订单
        - farmer（农户）：只能看到自己作为卖方的订单
        - 其他角色：能看到买卖双方的订单

        Returns:
            QuerySet: 过滤后的订单查询集
        """
        # select_related 预加载关联表，避免 N+1 查询
        # buyer, seller, product, trade_info 都会被预加载
        queryset = Order.objects.select_related(
            'buyer', 'seller', 'product', 'trade_info'
        ).all()

        # 获取当前用户的角色
        role = getattr(self.request.user, 'role', None)

        # 按角色过滤查询结果
        if role == 'buyer':
            # 采购商：只看买方订单
            queryset = queryset.filter(buyer=self.request.user)
        elif role == 'farmer':
            # 农户：只看卖方订单
            queryset = queryset.filter(seller=self.request.user)
        else:
            # 其他角色：同时查看买卖双方
            queryset = queryset.filter(
                buyer=self.request.user
            ) | queryset.filter(seller=self.request.user)

        # 去重（避免同一订单被两个过滤条件匹配）
        # 按创建时间倒序排列（最新的在前）
        return queryset.distinct().order_by('-created_at')

    def get_serializer_class(self):
        """
        根据动作返回不同的序列化器

        不同场景使用不同序列化器：
        - create（创建订单）：使用 OrderCreateSerializer（含验证逻辑）
        - accept_order（接受订单）：使用 OrderAcceptSerializer
        - 其他动作：使用 OrderSerializer（只读/更新）
        """
        if self.action == 'create':
            return OrderCreateSerializer
        if self.action == 'accept_order':
            return OrderAcceptSerializer
        return OrderSerializer

    @action(detail=False, methods=['get'])
    def my_orders(self, request):
        """
        获取当前用户的订单列表（支持状态过滤）

        URL: GET /orders/my_orders/
        URL: GET /orders/my_orders/?status=pending
        Returns: 分页的订单列表

        使用 get_queryset() 获取按角色过滤后的查询集
        """
        queryset = self.get_queryset()

        # 可选：按状态过滤（?status=pending）
        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        # 分页返回
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def accept_order(self, request):
        """
        农户接受采购商发布的求购订单

        URL: POST /orders/accept_order/
        业务逻辑：
        1. 农户（卖方）选择一条采购商发布的求购信息
        2. 填写价格、数量等信息
        3. 系统自动创建订单，农户为卖方，采购商为买方
        4. 供需信息状态更新为已成交

        注意：这是农户"接单"的场景，与采购商"下单"不同
        """
        # 导入并验证数据
        from .serializers import OrderAcceptSerializer
        serializer = OrderAcceptSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # 获取要接受的供需信息
        trade_info = serializer.validated_data['trade_info']
        user = request.user

        # ========== 前置条件检查 ==========

        # 不能接受自己发布的求购信息
        if trade_info.publisher == user:
            return Response(
                {'error': '不能接受自己发布的订单'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 只能接受求购类型（demand）的供需信息
        if trade_info.info_type != 'demand':
            return Response(
                {'error': '只能接受求购信息'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 供需信息必须是活跃状态
        if trade_info.status != 'active':
            return Response(
                {'error': '该供需信息已结束'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # ========== 事务操作 ==========
        # 使用事务确保数据一致性：订单创建、状态更新、日志记录要么全部成功，要么全部回滚
        with transaction.atomic():
            # 创建订单
            order = Order.objects.create(
                buyer=trade_info.publisher,  # 采购商是买方（供需信息发布者）
                seller=user,                  # 当前农户是卖方（接受订单的人）
                trade_info=trade_info,        # 关联的供需信息
                product=serializer.validated_data['product'],           # 农产品
                quantity=serializer.validated_data['quantity'],         # 数量
                unit=serializer.validated_data.get('unit', '斤'),      # 单位
                unit_price=serializer.validated_data.get('unit_price', 0),  # 单价
                buyer_contact=serializer.validated_data.get('buyer_contact', ''),      # 买方联系方式
                delivery_address=serializer.validated_data.get('delivery_address', ''),  # 收货地址
                remark=serializer.validated_data.get('remark', '')      # 备注
            )

            # 将供需信息标记为已成交
            trade_info.status = 'completed'
            trade_info.save()

            # 记录状态变更日志
            OrderStatusLog.objects.create(
                order=order,
                to_status='pending',   # 初始状态为待确认
                operator=user,         # 操作人是接受订单的农户
                remark='接受订单'
            )

        # 返回创建的订单信息
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        """
        卖方确认订单

        URL: POST /orders/{id}/confirm/
        权限：只有卖方能操作
        前置状态：pending（待确认）
        """
        order = self.get_object()

        # 权限检查：只有卖方能确认
        if order.seller != request.user:
            return Response({'error': '无权限操作'}, status=status.HTTP_403_FORBIDDEN)

        # 状态检查：必须是待确认状态
        if order.status != 'pending':
            return Response({'error': '订单状态不允许确认'}, status=status.HTTP_400_BAD_REQUEST)

        # 记录原状态
        old_status = order.status

        # 更新状态
        order.status = 'confirmed'
        order.save()

        # 记录状态变更日志
        OrderStatusLog.objects.create(
            order=order,
            from_status=old_status,           # 原状态
            to_status='confirmed',            # 新状态
            operator=request.user,            # 操作人
            remark='确认订单'
        )

        return Response({'message': '订单已确认'})

    @action(detail=True, methods=['post'])
    def ship(self, request, pk=None):
        """
        卖方发货

        URL: POST /orders/{id}/ship/
        权限：只有卖方能操作
        前置状态：confirmed（已确认）
        """
        order = self.get_object()

        # 权限检查
        if order.seller != request.user:
            return Response({'error': '无权限操作'}, status=status.HTTP_403_FORBIDDEN)

        # 状态检查：必须是已确认状态
        if order.status != 'confirmed':
            return Response({'error': '订单状态不允许发货'}, status=status.HTTP_400_BAD_REQUEST)

        # 记录原状态
        old_status = order.status

        # 更新状态
        order.status = 'shipped'
        order.save()

        # 记录日志
        OrderStatusLog.objects.create(
            order=order,
            from_status=old_status,
            to_status='shipped',
            operator=request.user,
            remark='已发货'
        )

        return Response({'message': '已发货'})

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """
        买方确认收货，完成订单

        URL: POST /orders/{id}/complete/
        权限：只有买方能操作
        前置状态：shipped（已发货）
        """
        order = self.get_object()

        # 权限检查：只有买方能确认收货
        if order.buyer != request.user:
            return Response({'error': '无权限操作'}, status=status.HTTP_403_FORBIDDEN)

        # 状态检查：必须是已发货状态
        if order.status != 'shipped':
            return Response({'error': '订单状态不允许完成'}, status=status.HTTP_400_BAD_REQUEST)

        # 记录原状态
        old_status = order.status

        # 更新状态
        order.status = 'completed'
        order.save()

        # 记录日志
        OrderStatusLog.objects.create(
            order=order,
            from_status=old_status,
            to_status='completed',
            operator=request.user,
            remark='确认收货'
        )

        return Response({'message': '订单已完成'})

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        取消订单

        URL: POST /orders/{id}/cancel/
        权限：买方或卖方都能取消
        禁止状态：已完成（completed）或已取消（cancelled）的订单不能取消
        """
        order = self.get_object()

        # 权限检查：买卖双方都能取消
        if order.buyer != request.user and order.seller != request.user:
            return Response({'error': '无权限操作'}, status=status.HTTP_403_FORBIDDEN)

        # 状态检查：已完成或已取消的不能再次取消
        if order.status in ['completed', 'cancelled']:
            return Response({'error': '订单状态不允许取消'}, status=status.HTTP_400_BAD_REQUEST)

        # 记录原状态
        old_status = order.status

        # 更新状态
        order.status = 'cancelled'
        order.save()

        # 如果订单关联了供需信息，将供需信息状态恢复为 active（可重新交易）
        if order.trade_info:
            order.trade_info.status = 'active'
            order.trade_info.save()

        # 记录日志
        OrderStatusLog.objects.create(
            order=order,
            from_status=old_status,
            to_status='cancelled',
            operator=request.user,
            remark='取消订单'
        )

        return Response({'message': '订单已取消'})
