from django.db import models


class SystemConfig(models.Model):
    """系统配置"""

    PUSH_STRATEGY_CHOICES = [
        ('all', '全员推送'),
        ('farmers_only', '仅农户'),
        ('buyers_only', '仅采购商'),
        ('none', '关闭推送'),
    ]

    key = models.CharField(max_length=100, unique=True, verbose_name='配置键')
    value = models.CharField(max_length=500, blank=True, verbose_name='配置值')
    description = models.CharField(max_length=200, blank=True, verbose_name='描述')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'system_config'
        verbose_name = '系统配置'
        verbose_name_plural = '系统配置'

    def __str__(self):
        return f"{self.key} = {self.value}"

    @classmethod
    def get_value(cls, key, default=None):
        try:
            return cls.objects.get(key=key).value
        except cls.DoesNotExist:
            return default

    @classmethod
    def set_value(cls, key, value, description=''):
        obj, _ = cls.objects.update_or_create(
            key=key,
            defaults={'value': str(value), 'description': description}
        )
        return obj


# 配置键常量
CONFIG_PRICE_DROP_THRESHOLD = 'price_drop_threshold'
CONFIG_PRICE_RISE_THRESHOLD = 'price_rise_threshold'
CONFIG_PUSH_STRATEGY = 'push_strategy'
CONFIG_PREDICTION_DAYS = 'prediction_days'

# 默认值
DEFAULT_PRICE_DROP_THRESHOLD = 10
DEFAULT_PRICE_RISE_THRESHOLD = 15
DEFAULT_PUSH_STRATEGY = 'all'
DEFAULT_PREDICTION_DAYS = 14
