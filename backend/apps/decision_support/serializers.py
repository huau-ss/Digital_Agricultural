# Django REST Framework 序列化器
# 序列化器的作用：在 Django 模型和 JSON 数据之间做转换
# - 序列化（Serializer）：模型 → JSON（后端 → 前端）
# - 反序列化（Deserializer）：JSON → 模型（前端 → 后端）
from rest_framework import serializers

# 导入本 app 的模型
from .models import TradeInfo, Order, OrderStatusLog
# 导入农产品模型（来自 data_collection app）
from apps.data_collection.models import AgriculturalProduct


# =============================================================================
# TradeInfoSerializer - 供需信息序列化器
# 用于供需信息的序列化和反序列化
# =============================================================================
class TradeInfoSerializer(serializers.ModelSerializer):
    """
    供需信息序列化器

    功能：
    1. 序列化：将 TradeInfo 模型实例转换为 JSON（供前端展示）
    2. 反序列化：验证前端提交的 JSON 数据，创建/更新 TradeInfo

    字段说明：
    - 原始字段：直接从模型读取（如 info_type, quantity）
    - 计算字段：通过 source='xxx.yyy' 获取关联对象的属性（如 publisher_name）
    - 显示字段：使用 get_xxx_display() 获取 choices 的中文描述
    """

    # ========== 关联对象字段（只读）==========
    # source='publisher.username' 表示从 publisher 关联对象获取 username 属性
    # read_only=True 表示这些字段只在序列化时使用，不接受前端输入
    publisher_name = serializers.CharField(
        source='publisher.username',
        read_only=True
    )
    publisher_role = serializers.CharField(
        source='publisher.role',
        read_only=True
    )
    product_name = serializers.CharField(
        source='product.name',
        read_only=True
    )

    # ========== 状态显示字段（只读）==========
    # Django 的 CharField choices 会自动生成 get_xxx_display() 方法
    # 例如：status='active' → get_status_display() 返回'进行中'
    info_type_display = serializers.CharField(
        source='get_info_type_display',
        read_only=True
    )
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )

    class Meta:
        # 指定对应的模型
        model = TradeInfo

        # 指定序列化的字段
        # 包含：主键、发布者信息、供需类型、产品信息、数量价格、状态、联系方式等
        fields = [
            'id',                              # 供需信息ID
            'publisher',                      # 发布者ID（外键）
            'publisher_name',                  # 发布者用户名（计算字段）
            'publisher_role',                  # 发布者角色（计算字段）
            'info_type',                       # 供需类型（supply=供应/demand=求购）
            'info_type_display',               # 供需类型中文显示
            'product',                         # 农产品ID（外键）
            'product_name',                    # 农产品名称（计算字段）
            'quantity',                        # 数量
            'unit',                           # 单位
            'expected_price',                 # 期望价格
            'origin',                         # 产地
            'contact_phone',                  # 联系电话
            'description',                    # 描述
            'status',                         # 状态（active/completed/cancelled）
            'status_display',                 # 状态中文显示
            'created_at',                     # 创建时间
            'updated_at'                      # 更新时间
        ]

        # 只读字段：创建时由系统自动生成，不接受前端输入
        read_only_fields = ['publisher', 'created_at', 'updated_at']

    def validate(self, data):
        """
        字段级别验证之后的对象级别验证

        业务规则验证：
        1. 农户（farmer）只能发布供应信息（supply），不能发布求购信息（demand）
        2. 采购商（buyer）只能发布求购信息（demand），不能发布供应信息（supply）

        Args:
            data: 验证后的字段数据字典

        Returns:
            验证通过返回 data，失败抛出 ValidationError
        """
        # self.instance 不为空表示是更新操作，跳过验证
        if self.instance:
            return data

        # 从 context 中获取当前请求和用户
        user = self.context.get('request', {}).user

        # 未登录用户不验证（IsAuthenticated 权限会在之前拦截）
        if not user or not user.is_authenticated:
            return data

        # 获取要创建的供需类型
        info_type = data.get('info_type')

        # 检查用户角色并验证
        if hasattr(user, 'role'):
            # 农户不能发布求购信息
            if user.role == 'farmer' and info_type == 'demand':
                raise serializers.ValidationError({
                    'info_type': '农户只能发布供应信息'
                })
            # 采购商不能发布供应信息
            if user.role == 'buyer' and info_type == 'supply':
                raise serializers.ValidationError({
                    'info_type': '采购商只能发布求购信息'
                })

        return data

    def create(self, validated_data):
        """
        创建供需信息

        重写 create 方法，自动设置发布者为当前登录用户

        Args:
            validated_data: 通过验证的字段数据

        Returns:
            创建的 TradeInfo 实例
        """
        # 从 context 中获取当前请求
        request = self.context.get('request')

        # 如果有请求且请求中有用户，设置发布者
        if request and hasattr(request, 'user'):
            validated_data['publisher'] = request.user

        # 调用父类的 create 方法完成创建
        return super().create(validated_data)


# =============================================================================
# OrderSerializer - 订单序列化器
# 用于订单的序列化和反序列化（包含完整信息展示）
# =============================================================================
class OrderSerializer(serializers.ModelSerializer):
    """
    订单序列化器

    用于：
    1. 订单列表/详情展示（序列化）
    2. 订单更新（反序列化）

    注意：创建订单使用 OrderCreateSerializer
    """

    # ========== 买方信息字段（只读）==========
    # source='buyer.id' 获取关联对象 buyer 的 id
    buyer_id = serializers.IntegerField(
        source='buyer.id',
        read_only=True,
        allow_null=True  # 允许为空（订单可能没有关联用户）
    )
    buyer_name = serializers.CharField(
        source='buyer.username',
        read_only=True,
        allow_null=True
    )

    # ========== 卖方信息字段（只读）==========
    seller_id = serializers.IntegerField(
        source='seller.id',
        read_only=True,
        allow_null=True
    )
    seller_name = serializers.CharField(
        source='seller.username',
        read_only=True,
        allow_null=True
    )

    # ========== 产品和订单信息字段（只读）==========
    product_name = serializers.CharField(
        source='product.name',
        read_only=True
    )
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    trade_info_id = serializers.IntegerField(
        source='trade_info.id',
        read_only=True,
        allow_null=True
    )

    class Meta:
        model = Order
        fields = [
            # 基本信息
            'id',                              # 订单ID
            'order_no',                        # 订单号（自动生成）
            # 买方信息
            'buyer',                           # 买方ID（外键）
            'buyer_id',                        # 买方ID（计算字段）
            'buyer_name',                      # 买方用户名
            # 卖方信息
            'seller',                          # 卖方ID（外键）
            'seller_id',                       # 卖方ID（计算字段）
            'seller_name',                      # 卖方用户名
            # 关联信息
            'trade_info',                      # 供需信息ID（外键）
            'trade_info_id',                   # 供需信息ID（计算字段）
            # 产品和价格信息
            'product',                         # 农产品ID
            'product_name',                    # 农产品名称
            'quantity',                        # 数量
            'unit',                           # 单位
            'unit_price',                     # 单价
            'total_amount',                    # 总金额（自动计算）
            # 订单状态
            'status',                         # 状态
            'status_display',                  # 状态中文显示
            # 联系方式和地址
            'buyer_contact',                  # 买方联系方式
            'seller_contact',                  # 卖方联系方式
            'delivery_address',               # 收货地址
            'remark',                         # 备注
            # 时间戳
            'created_at',                     # 创建时间
            'updated_at'                      # 更新时间
        ]

        # 只读字段：自动生成的字段，不接受前端输入
        read_only_fields = [
            'order_no',   # 自动生成
            'buyer',      # 自动设置
            'seller',     # 自动设置
            'total_amount',  # 自动计算
            'created_at', 'updated_at'  # 自动时间戳
        ]


# =============================================================================
# OrderCreateSerializer - 创建订单序列化器
# 专门用于创建新订单，包含创建时的业务逻辑
# =============================================================================
class OrderCreateSerializer(serializers.ModelSerializer):
    """
    创建订单序列化器

    用途：采购商在供需大厅看到供应信息后，点击"立即购买"创建订单

    业务逻辑：
    1. 验证供需信息状态（必须是 active）
    2. 验证不能购买自己发布的信息
    3. 创建订单时自动设置买方为当前用户
    4. 自动将供需信息状态改为已完成
    5. 创建订单状态日志
    """

    class Meta:
        model = Order
        # 创建订单时需要提交的字段
        fields = [
            'trade_info',              # 关联的供需信息（必填）
            'product',                # 农产品
            'quantity',               # 数量（必填）
            'unit',                   # 单位
            'unit_price',             # 单价
            'buyer_contact',          # 买方联系方式
            'delivery_address',       # 收货地址
            'remark'                  # 备注
        ]

    def validate(self, data):
        """
        验证创建订单的数据

        验证规则：
        1. 用户必须登录
        2. 不能购买自己发布的供需信息
        3. 供需信息必须是活跃状态（active）
        """
        request = self.context.get('request')

        # 检查登录状态
        if not request or not request.user:
            raise serializers.ValidationError('需要登录才能创建订单')

        # 获取要购买的供需信息
        trade_info = data.get('trade_info')
        if trade_info:
            # 不能购买自己发布的
            if trade_info.publisher == request.user:
                raise serializers.ValidationError('不能购买自己发布的商品')

            # 供需信息必须处于活跃状态
            if trade_info.status != 'active':
                raise serializers.ValidationError('该供需信息已结束')

        return data

    def create(self, validated_data):
        """
        创建订单

        业务逻辑：
        1. 设置买方为当前用户
        2. 设置卖方为供需信息的发布者
        3. 自动填充买方联系方式
        4. 将供需信息标记为已完成
        5. 创建订单状态日志

        Args:
            validated_data: 验证通过的数据

        Returns:
            创建的 Order 实例
        """
        request = self.context.get('request')
        user = request.user

        # 从数据中分离出 trade_info（需要特殊处理）
        trade_info = validated_data.pop('trade_info', None)

        # 创建订单实例
        order = Order(
            buyer=user,                           # 买方 = 当前用户（采购商）
            seller=trade_info.publisher if trade_info else None,  # 卖方 = 供需信息发布者
            trade_info=trade_info,                # 关联的供需信息
            # 如果没有提供买方联系方式，使用用户的电话
            buyer_contact=validated_data.get('buyer_contact', user.phone or ''),
            unit='斤'                             # 默认单位
        )

        # 设置产品、数量、单价等字段
        for field in ['product', 'quantity', 'unit_price']:
            if field in validated_data:
                setattr(order, field, validated_data[field])

        # 保存订单（会触发 Order 模型的 save() 方法，自动生成订单号和计算总金额）
        order.save()

        # 将关联的供需信息标记为已完成
        if trade_info:
            trade_info.status = 'completed'
            trade_info.save()

        # 创建订单状态日志（记录订单创建）
        OrderStatusLog.objects.create(
            order=order,
            to_status='pending',        # 初始状态为待确认
            operator=user,              # 操作人是买方
            remark='创建订单'
        )

        return order


# =============================================================================
# OrderAcceptSerializer - 接受订单序列化器
# 专门用于农户接受采购商发布的求购订单
# =============================================================================
class OrderAcceptSerializer(serializers.Serializer):
    """
    接受订单序列化器

    用途：农户在供需大厅看到采购商的求购信息后，点击"我要供货"接受订单

    这是 Serializer 而不是 ModelSerializer，因为：
    - 不直接对应 Order 模型
    - 字段验证和创建逻辑在 views.py 的 accept_order 中处理

    与 OrderCreateSerializer 的区别：
    - OrderCreateSerializer：采购商主动下单（买→卖）
    - OrderAcceptSerializer：农户主动接单（卖→买）
    """

    # ========== 必填字段 ==========

    # PrimaryKeyRelatedField：接收主键 ID，自动验证对应记录是否存在
    # queryset 指定可选范围，required=True 表示必填
    trade_info = serializers.PrimaryKeyRelatedField(
        queryset=TradeInfo.objects.all(),
        help_text='要接受的供需信息ID'
    )

    # DecimalField：精确小数，用于金额和数量
    # max_digits=10：总位数不超过10
    # decimal_places=2：小数点后2位
    quantity = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text='供应数量'
    )

    # ========== 可选字段 ==========

    # required=False：可选字段
    # allow_null=True：允许传入 null
    product = serializers.PrimaryKeyRelatedField(
        queryset=AgriculturalProduct.objects.all(),
        required=False,
        help_text='农产品ID'
    )
    unit = serializers.CharField(
        max_length=20,
        default='斤',
        help_text='单位'
    )
    unit_price = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        allow_null=True,
        help_text='单价'
    )
    buyer_contact = serializers.CharField(
        max_length=20,
        required=False,
        allow_blank=True,
        help_text='买方联系方式'
    )
    delivery_address = serializers.CharField(
        max_length=200,
        required=False,
        allow_blank=True,
        help_text='收货地址'
    )
    remark = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text='备注'
    )
