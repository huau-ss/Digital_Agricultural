from django.db import models


class AgriculturalProduct(models.Model):
    """农产品基本信息"""
    CATEGORY_CHOICES = [
        ('vegetable', '蔬菜'),
        ('fruit', '水果'),
        ('livestock', '畜禽'),
        ('aquatic', '水产'),
        ('grain', '粮油'),
        ('other', '其他'),
    ]

    name = models.CharField(max_length=100, verbose_name='品名')
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        verbose_name='类别'
    )
    origin = models.CharField(max_length=200, verbose_name='产地', blank=True)
    unit = models.CharField(max_length=20, default='CNY/kg', verbose_name='单位')
    description = models.TextField(verbose_name='描述', blank=True)
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'agricultural_products'
        verbose_name = '农产品'
        verbose_name_plural = '农产品'
        ordering = ['category', 'name']

    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"


class PriceHistory(models.Model):
    """历史价格数据"""
    product = models.ForeignKey(
        AgriculturalProduct,
        on_delete=models.CASCADE,
        related_name='price_history',
        verbose_name='关联产品'
    )
    date = models.DateField(verbose_name='日期')
    market_name = models.CharField(max_length=200, verbose_name='市场名称')
    avg_price = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        verbose_name='平均价格'
    )
    max_price = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        null=True,
        blank=True,
        verbose_name='最高价'
    )
    min_price = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        null=True,
        blank=True,
        verbose_name='最低价'
    )
    volume = models.BigIntegerField(null=True, blank=True, verbose_name='交易量')
    source = models.CharField(max_length=100, blank=True, verbose_name='数据来源')
    remarks = models.TextField(blank=True, verbose_name='备注')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        db_table = 'price_history'
        verbose_name = '历史价格'
        verbose_name_plural = '历史价格'
        ordering = ['-date', 'market_name']
        indexes = [
            models.Index(fields=['date']),
            models.Index(fields=['market_name']),
            models.Index(fields=['product', 'date']),
        ]
        unique_together = ['product', 'market_name', 'date']

    def __str__(self):
        return f"{self.product.name} - {self.market_name} - {self.date}"


class CleanedPriceData(models.Model):
    """清洗后的历史价格数据"""
    product = models.ForeignKey(
        AgriculturalProduct,
        on_delete=models.CASCADE,
        related_name='cleaned_price_data',
        verbose_name='关联产品'
    )
    date = models.DateField(verbose_name='日期')
    market_name = models.CharField(max_length=200, verbose_name='市场名称')
    avg_price = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        verbose_name='平均价格'
    )
    max_price = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        null=True,
        blank=True,
        verbose_name='最高价'
    )
    min_price = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        null=True,
        blank=True,
        verbose_name='最低价'
    )
    volume = models.BigIntegerField(null=True, blank=True, verbose_name='交易量')
    source = models.CharField(max_length=100, blank=True, verbose_name='数据来源')
    is_outlier = models.BooleanField(default=False, verbose_name='是否为异常值')
    outlier_reason = models.CharField(max_length=100, blank=True, verbose_name='异常原因')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        db_table = 'cleaned_price_data'
        verbose_name = '清洗后价格'
        verbose_name_plural = '清洗后价格'
        ordering = ['-date', 'market_name']
        indexes = [
            models.Index(fields=['date']),
            models.Index(fields=['market_name']),
            models.Index(fields=['product', 'date']),
            models.Index(fields=['is_outlier']),
        ]
        unique_together = ['product', 'market_name', 'date']

    def __str__(self):
        return f"{self.product.name} - {self.market_name} - {self.date}"
