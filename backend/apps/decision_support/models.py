from django.db import models
from django.conf import settings
from django.utils import timezone


class TradeInfo(models.Model):
    """供需信息模型"""

    INFO_TYPE_CHOICES = [
        ('supply', '供应'),
        ('demand', '求购'),
    ]

    STATUS_CHOICES = [
        ('active', '进行中'),
        ('completed', '已成交'),
        ('expired', '已过期'),
        ('cancelled', '已取消'),
    ]

    publisher = models.ForeignKey(
        settings.AUTH_USER_MODEL,      # 关联 Django 内置 User 表
        on_delete=models.CASCADE,       # 用户删除时，级联删除其发布的所有供需信息
        related_name='trade_infos',     # 反向查询：user.trade_infos.all()
        verbose_name='发布者'
    )
    info_type = models.CharField(
        max_length=10,
        choices=INFO_TYPE_CHOICES,
        verbose_name='信息类型'
    )
    product = models.ForeignKey(
        'data_collection.AgriculturalProduct',    # 关联农产品模型
        on_delete=models.CASCADE,                # 农产品删除时，级联删除其发布的所有供需信息
        related_name='trade_infos',              # 反向查询：product.trade_infos.all()
        verbose_name='农产品'
    )
    quantity = models.DecimalField(
        max_digits=10,                           # 最大位数
        decimal_places=2,                        # 小数位数
        verbose_name='数量'
    )
    unit = models.CharField(max_length=20, default='斤', verbose_name='单位')
    expected_price = models.DecimalField(
        max_digits=10,                           # 最大位数
        decimal_places=2,                        # 小数位数
        null=True,                               # 允许为空
        blank=True,                              # 允许为空
        verbose_name='期望价格(元/斤)'
    )
    origin = models.CharField(max_length=200, blank=True, verbose_name='产地')   # 产地
    contact_phone = models.CharField(max_length=20, blank=True, verbose_name='联系电话')   # 联系电话
    description = models.TextField(blank=True, verbose_name='详细信息')   # 详细信息
    status = models.CharField(
        max_length=20,                           # 最大长度
        choices=STATUS_CHOICES,                  # 状态选择
        default='active',                         # 默认状态
        verbose_name='状态'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='发布时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'trade_info'
        verbose_name = '供需信息'
        verbose_name_plural = '供需信息'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['info_type']),
            models.Index(fields=['status']),
            models.Index(fields=['product']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.get_info_type_display()} - {self.product.name} - {self.publisher.username}"


class Order(models.Model):
    """订单模型"""

    ORDER_STATUS_CHOICES = [
        ('pending', '待确认'),
        ('confirmed', '已确认'),
        ('shipped', '已发货'),
        ('completed', '已完成'),
        ('cancelled', '已取消'),
    ]

    order_no = models.CharField(max_length=32, unique=True, verbose_name='订单编号')
    buyer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='buyer_orders',
        verbose_name='买方'
    )
    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='seller_orders',
        verbose_name='卖方'
    )
    trade_info = models.ForeignKey(
        TradeInfo,                                    # 关联供需信息模型
        on_delete=models.SET_NULL,                     # 供需信息删除时，设置为空
        null=True,                                     # 允许为空
        blank=True,                                    # 允许为空
        related_name='orders',                         # 反向查询：trade_info.orders.all()
        verbose_name='关联供需信息'
    )
    product = models.ForeignKey(
        'data_collection.AgriculturalProduct',        # 关联农产品模型
        on_delete=models.CASCADE,                     # 农产品删除时，级联删除其发布的所有订单
        related_name='orders',                         # 反向查询：product.orders.all()
        verbose_name='农产品'
    )
    quantity = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='数量')    # 数量
    unit = models.CharField(max_length=20, default='斤', verbose_name='单位')    # 单位
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='单价(元/斤)')    # 单价
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='总金额')    # 总金额
    status = models.CharField(
        max_length=20,                                # 最大长度
        choices=ORDER_STATUS_CHOICES,                  # 订单状态选择
        default='pending',                             # 默认状态
        verbose_name='订单状态'
    )
    buyer_contact = models.CharField(max_length=20, blank=True, verbose_name='买方联系方式')    # 买方联系方式
    seller_contact = models.CharField(max_length=20, blank=True, verbose_name='卖方联系方式')    # 卖方联系方式
    delivery_address = models.CharField(max_length=200, blank=True, verbose_name='收货地址')
    remark = models.TextField(blank=True, verbose_name='备注')    # 备注
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')    # 创建时间
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')    # 更新时间 

    # 元数据
    class Meta:
        db_table = 'order'
        verbose_name = '订单'
        verbose_name_plural = '订单'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['order_no']),
            models.Index(fields=['buyer']),
            models.Index(fields=['seller']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.order_no} - {self.product.name}"

    def save(self, *args, **kwargs):
        # 生成订单编号
        if not self.order_no:
            import uuid
            self.order_no = f"ORD{timezone.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:6].upper()}"
        # 计算总金额
        if self.unit_price and self.quantity:
            self.total_amount = self.unit_price * self.quantity
        super().save(*args, **kwargs)


class OrderStatusLog(models.Model):
    """订单状态变更日志"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='status_logs')    # 关联订单模型
    from_status = models.CharField(max_length=20, blank=True, verbose_name='原状态')
    to_status = models.CharField(max_length=20, verbose_name='新状态')
    operator = models.ForeignKey(
        settings.AUTH_USER_MODEL,       # 关联 Django 内置 User 表
        on_delete=models.SET_NULL,      # 用户删除时，设置为空
        null=True,                       # 允许为空
        verbose_name='操作人'
    )
    remark = models.TextField(blank=True, verbose_name='备注')    # 备注
    created_at = models.DateTimeField(auto_now_add=True)    # 创建时间  

    class Meta:
        db_table = 'order_status_log'
        verbose_name = '订单状态日志'
        verbose_name_plural = '订单状态日志'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.order.order_no} - {self.from_status} -> {self.to_status}"
