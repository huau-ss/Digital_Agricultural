from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    """自定义用户模型"""

    ROLE_CHOICES = [
        ('farmer', '农户'),
        ('buyer', '采购商'),
        ('admin', '系统管理员'),
    ]

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='farmer',
        verbose_name='用户角色'
    )
    phone = models.CharField(max_length=20, blank=True, verbose_name='手机号')
    address = models.CharField(max_length=255, blank=True, verbose_name='地址')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'users'
        verbose_name = '用户'
        verbose_name_plural = '用户'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


class SystemMessage(models.Model):
    """系统消息/预警模型"""

    TYPE_CHOICES = [
        ('price_warning', '价格预警'),
        ('price_alert', '价格提醒'),
        ('system', '系统通知'),
        ('order', '订单通知'),
    ]

    PRIORITY_CHOICES = [
        ('low', '低'),
        ('medium', '中'),
        ('high', '高'),
        ('urgent', '紧急'),
    ]

    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='system_messages',
        verbose_name='接收用户'
    )
    title = models.CharField(max_length=200, verbose_name='消息标题')
    content = models.TextField(verbose_name='消息内容')
    message_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default='system',
        verbose_name='消息类型'
    )
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='medium',
        verbose_name='优先级'
    )
    is_read = models.BooleanField(default=False, verbose_name='是否已读')
    related_product_id = models.IntegerField(null=True, blank=True, verbose_name='关联产品ID')
    related_product_name = models.CharField(max_length=100, blank=True, verbose_name='关联产品名称')
    price_change_percent = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='价格变动百分比'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    read_at = models.DateTimeField(null=True, blank=True, verbose_name='阅读时间')

    class Meta:
        db_table = 'system_messages'
        verbose_name = '系统消息'
        verbose_name_plural = '系统消息'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.title}"

    def mark_as_read(self):
        """标记消息为已读"""
        if not self.is_read:
            from django.utils import timezone
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])
