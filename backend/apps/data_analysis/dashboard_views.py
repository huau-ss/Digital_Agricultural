# -*- coding: utf-8 -*-
"""
Dashboard 仪表盘数据聚合 API
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Q
from datetime import datetime, timedelta

from apps.data_collection.models import AgriculturalProduct, CleanedPriceData
from apps.decision_support.models import TradeInfo
from apps.users.models import SystemMessage
from .lstm_service import predict_product_price, get_product_price_history


class DashboardSummaryView(APIView):
    """仪表盘汇总数据"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        GET /api/dashboard/summary/
        返回仪表盘聚合数据
        """
        try:
            # 1. 统计数据
            stats = self.get_stats()

            # 2. AI 涨势预测 TOP 5
            predict_top5 = self.get_predict_top5()

            # 3. 最新供需动态
            recent_trades = self.get_recent_trades()

            return Response({
                'code': 200,
                'message': '获取成功',
                'data': {
                    'stats': stats,
                    'predict_top5': predict_top5,
                    'recent_trades': recent_trades
                }
            })
        except Exception as e:
            return Response({
                'code': 500,
                'message': f'获取失败: {str(e)}',
                'data': None
            })

    def get_stats(self):
        """获取统计数据"""
        today = datetime.now().date()

        # 监控产品总数
        product_count = AgriculturalProduct.objects.filter(is_active=True).count()

        # 今日预警总数
        warning_count = SystemMessage.objects.filter(
            created_at__date=today,
            message_type='price_warning'
        ).count()

        # 供需信息总数
        trade_count = TradeInfo.objects.filter(status='active').count()

        return {
            'product_count': product_count,
            'warning_count': warning_count,
            'trade_count': trade_count,
            'user_count': 0  # 可以根据需要添加用户统计
        }

    def get_predict_top5(self):
        """获取涨幅最高的 5 个农产品预测"""
        # 获取所有活跃产品
        products = AgriculturalProduct.objects.filter(is_active=True)

        predictions = []

        for product in products:
            try:
                # 获取当前价格
                latest_price = CleanedPriceData.objects.filter(
                    product=product
                ).order_by('-date').first()

                if not latest_price:
                    continue

                current_price = float(latest_price.avg_price) / 2  # 转为斤的价格

                if current_price <= 0:
                    continue

                # 获取历史数据
                historical_prices = get_product_price_history(product.id, days=60)

                if len(historical_prices) < 15:
                    continue

                # 尝试加载模型进行预测
                from .lstm_service import LSTMPredictor

                predictor = LSTMPredictor(product.id)

                if predictor.load_model():
                    # 进行 14 天预测
                    dates, prices, is_prediction = predictor.predict_future(
                        historical_prices, future_days=14
                    )

                    # 找到预测最高价
                    future_prices = [p for p, is_p in zip(prices, is_prediction) if is_p]
                    if future_prices:
                        max_predicted_price = max(future_prices)
                        max_day_index = future_prices.index(max_predicted_price) + 1

                        # 计算涨幅
                        change_percent = ((max_predicted_price - current_price) / current_price) * 100

                        if change_percent > 0:  # 只添加上涨的
                            predictions.append({
                                'product_id': product.id,
                                'product_name': product.name,
                                'category': product.category,
                                'current_price': round(current_price, 2),
                                'predicted_max_price': round(max_predicted_price, 2),
                                'change_percent': round(change_percent, 2),
                                'change_day': max_day_index,
                                'unit': '元/斤'
                            })
                else:
                    # 如果没有模型，使用简单的趋势分析
                    if len(historical_prices) >= 7:
                        recent_avg = sum(historical_prices[-7:]) / 7
                        earlier_avg = sum(historical_prices[-14:-7]) / 7 if len(historical_prices) >= 14 else recent_avg

                        if earlier_avg > 0:
                            change_percent = ((recent_avg - earlier_avg) / earlier_avg) * 100

                            if change_percent > 0:
                                predictions.append({
                                    'product_id': product.id,
                                    'product_name': product.name,
                                    'category': product.category,
                                    'current_price': round(current_price, 2),
                                    'predicted_max_price': round(recent_avg, 2),
                                    'change_percent': round(change_percent, 2),
                                    'change_day': 7,
                                    'unit': '元/斤',
                                    'is_estimated': True  # 标记为估算值
                                })

            except Exception as e:
                continue

        # 按涨幅排序，取前 5
        predictions.sort(key=lambda x: x['change_percent'], reverse=True)
        top5 = predictions[:5]

        # 如果不足 5 个，添加一些示例数据
        if len(top5) < 5:
            sample_data = [
                {'product_name': '大蒜', 'change_percent': 18.5, 'current_price': 5.2, 'category': 'vegetable'},
                {'product_name': '生姜', 'change_percent': 15.3, 'current_price': 8.5, 'category': 'vegetable'},
                {'product_name': '辣椒', 'change_percent': 12.8, 'current_price': 4.8, 'category': 'vegetable'},
                {'product_name': '苹果', 'change_percent': 10.2, 'current_price': 6.5, 'category': 'fruit'},
                {'product_name': '土豆', 'change_percent': 8.5, 'current_price': 2.1, 'category': 'vegetable'},
            ]

            existing_names = [p['product_name'] for p in top5]
            for sample in sample_data:
                if sample['product_name'] not in existing_names and len(top5) < 5:
                    top5.append({
                        'product_id': 0,
                        'product_name': sample['product_name'],
                        'category': sample['category'],
                        'current_price': sample['current_price'],
                        'predicted_max_price': round(sample['current_price'] * (1 + sample['change_percent'] / 100), 2),
                        'change_percent': sample['change_percent'],
                        'change_day': 10,
                        'unit': '元/斤',
                        'is_sample': True  # 标记为示例数据
                    })

        return top5

    def get_recent_trades(self):
        """获取最新供需动态"""
        trades = TradeInfo.objects.filter(
            status='active'
        ).select_related('publisher', 'product').order_by('-created_at')[:10]

        result = []
        for trade in trades:
            # 脱敏手机号
            phone = trade.contact_phone
            if phone and len(phone) >= 7:
                phone = phone[:3] + '****' + phone[-4:]
            else:
                phone = '暂无'

            # 脱敏用户名
            username = trade.publisher.username
            if len(username) > 1:
                username = username[0] + '*' * (len(username) - 1)
            else:
                username = '*'

            result.append({
                'id': trade.id,
                'type': trade.info_type,
                'type_display': trade.get_info_type_display(),
                'publisher': username,
                'product_name': trade.product.name,
                'product_category': trade.product.category,
                'quantity': str(trade.quantity),
                'unit': trade.unit,
                'expected_price': str(trade.expected_price) if trade.expected_price else '面议',
                'origin': trade.origin or '未知',
                'contact_phone': phone,
                'created_at': trade.created_at.strftime('%m-%d %H:%M')
            })

        return result
