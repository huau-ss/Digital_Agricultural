from django.db import models
from django.conf import settings


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
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='trade_infos',
        verbose_name='发布者'
    )
    info_type = models.CharField(
        max_length=10,
        choices=INFO_TYPE_CHOICES,
        verbose_name='信息类型'
    )
    product = models.ForeignKey(
        'data_collection.AgriculturalProduct',
        on_delete=models.CASCADE,
        related_name='trade_infos',
        verbose_name='农产品'
    )
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='数量'
    )
    unit = models.CharField(max_length=20, default='斤', verbose_name='单位')
    expected_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='期望价格(元/斤)'
    )
    origin = models.CharField(max_length=200, blank=True, verbose_name='产地')
    contact_phone = models.CharField(max_length=20, blank=True, verbose_name='联系电话')
    description = models.TextField(blank=True, verbose_name='详细信息')
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
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
