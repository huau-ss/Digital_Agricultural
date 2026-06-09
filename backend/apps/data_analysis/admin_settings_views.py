# -*- coding: utf-8 -*-
"""
系统配置管理 API
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .system_config import (
    SystemConfig,
    CONFIG_PRICE_DROP_THRESHOLD,
    CONFIG_PRICE_RISE_THRESHOLD,
    CONFIG_PUSH_STRATEGY,
    CONFIG_PREDICTION_DAYS,
    DEFAULT_PRICE_DROP_THRESHOLD,
    DEFAULT_PRICE_RISE_THRESHOLD,
    DEFAULT_PUSH_STRATEGY,
    DEFAULT_PREDICTION_DAYS,
)


def _is_admin(request):
    return request.user.is_staff or request.user.role == 'admin'


class AdminSettingsView(APIView):
    """获取/更新系统配置"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not _is_admin(request):
            return Response({'code': 403, 'message': '无权限'}, status=status.HTTP_403_FORBIDDEN)

        drop_threshold = SystemConfig.get_value(
            CONFIG_PRICE_DROP_THRESHOLD, DEFAULT_PRICE_DROP_THRESHOLD
        )
        rise_threshold = SystemConfig.get_value(
            CONFIG_PRICE_RISE_THRESHOLD, DEFAULT_PRICE_RISE_THRESHOLD
        )
        push_strategy = SystemConfig.get_value(
            CONFIG_PUSH_STRATEGY, DEFAULT_PUSH_STRATEGY
        )
        prediction_days = SystemConfig.get_value(
            CONFIG_PREDICTION_DAYS, DEFAULT_PREDICTION_DAYS
        )

        # 初始化默认值（如果不存在）
        self._ensure_defaults()

        return Response({
            'code': 200,
            'message': '获取成功',
            'data': {
                'price_drop_threshold': float(drop_threshold),
                'price_rise_threshold': float(rise_threshold),
                'push_strategy': push_strategy,
                'prediction_days': int(prediction_days),
            }
        })

    def post(self, request):
        if not _is_admin(request):
            return Response({'code': 403, 'message': '无权限'}, status=status.HTTP_403_FORBIDDEN)

        data = request.data
        updated = []

        if 'price_drop_threshold' in data:
            val = float(data['price_drop_threshold'])
            if val < 0 or val > 100:
                return Response({'code': 400, 'message': '跌幅阈值范围 0-100'}, status=status.HTTP_400_BAD_REQUEST)
            SystemConfig.set_value(CONFIG_PRICE_DROP_THRESHOLD, val, '价格跌幅预警阈值(%)')
            updated.append('price_drop_threshold')

        if 'price_rise_threshold' in data:
            val = float(data['price_rise_threshold'])
            if val < 0 or val > 100:
                return Response({'code': 400, 'message': '涨幅阈值范围 0-100'}, status=status.HTTP_400_BAD_REQUEST)
            SystemConfig.set_value(CONFIG_PRICE_RISE_THRESHOLD, val, '价格涨幅预警阈值(%)')
            updated.append('price_rise_threshold')

        if 'push_strategy' in data:
            val = data['push_strategy']
            choices = [c[0] for c in SystemConfig.PUSH_STRATEGY_CHOICES]
            if val not in choices:
                return Response({'code': 400, 'message': f'推送策略必须是 {choices} 之一'}, status=status.HTTP_400_BAD_REQUEST)
            SystemConfig.set_value(CONFIG_PUSH_STRATEGY, val, '预警消息推送策略')
            updated.append('push_strategy')

        if 'prediction_days' in data:
            val = int(data['prediction_days'])
            if val < 1 or val > 30:
                return Response({'code': 400, 'message': '预测天数范围 1-30'}, status=status.HTTP_400_BAD_REQUEST)
            SystemConfig.set_value(CONFIG_PREDICTION_DAYS, val, '默认预测天数')
            updated.append('prediction_days')

        if not updated:
            return Response({'code': 400, 'message': '未提供有效配置项'}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'code': 200,
            'message': f'已更新: {", ".join(updated)}',
            'data': {'updated': updated}
        })

    def _ensure_defaults(self):
        """初始化默认值"""
        if not SystemConfig.objects.filter(key=CONFIG_PRICE_DROP_THRESHOLD).exists():
            SystemConfig.objects.create(
                key=CONFIG_PRICE_DROP_THRESHOLD,
                value=str(DEFAULT_PRICE_DROP_THRESHOLD),
                description='价格跌幅预警阈值(%)'
            )
        if not SystemConfig.objects.filter(key=CONFIG_PRICE_RISE_THRESHOLD).exists():
            SystemConfig.objects.create(
                key=CONFIG_PRICE_RISE_THRESHOLD,
                value=str(DEFAULT_PRICE_RISE_THRESHOLD),
                description='价格涨幅预警阈值(%)'
            )
        if not SystemConfig.objects.filter(key=CONFIG_PUSH_STRATEGY).exists():
            SystemConfig.objects.create(
                key=CONFIG_PUSH_STRATEGY,
                value=DEFAULT_PUSH_STRATEGY,
                description='预警消息推送策略'
            )
        if not SystemConfig.objects.filter(key=CONFIG_PREDICTION_DAYS).exists():
            SystemConfig.objects.create(
                key=CONFIG_PREDICTION_DAYS,
                value=str(DEFAULT_PREDICTION_DAYS),
                description='默认预测天数'
            )
