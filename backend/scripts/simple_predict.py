# -*- coding: utf-8 -*-
"""
简单的价格预测方法 - 基于指数移动平均
适用于数据量有限的情况
"""
import os, sys
sys.path.insert(0, '.')
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'configs.settings')
django.setup()

from apps.data_analysis.lstm_service import get_product_price_history
from apps.data_collection.models import CleanedPriceData
import numpy as np
from datetime import datetime, timedelta

def predict_with_ema(product_id, future_days=7, alpha=0.3):
    """
    使用指数移动平均预测
    alpha: 平滑系数，0-1之间，越大越重视近期数据
    """
    history = get_product_price_history(product_id, days=30)

    if len(history) < 7:
        return {'success': False, 'error': '数据不足'}

    # 计算 EMA
    ema = history[0]
    for price in history[1:]:
        ema = alpha * price + (1 - alpha) * ema

    # 简单趋势调整
    recent_trend = np.mean(np.diff(history[-7:]))

    predictions = []
    for i in range(future_days):
        # 考虑趋势衰减
        trend_factor = 1 - (i * 0.05)  # 趋势影响力递减
        pred = ema + recent_trend * trend_factor * (i + 1) * 0.3
        predictions.append(round(max(0, pred), 2))

    return {
        'success': True,
        'method': 'EMA',
        'ema': round(ema, 2),
        'recent_trend': round(recent_trend, 4),
        'predictions': predictions,
        'history_mean': round(np.mean(history), 2),
        'history_std': round(np.std(history), 2)
    }


def predict_with_seasonal(product_id, future_days=7):
    """
    使用季节性调整的预测
    考虑周末效应和季节效应
    """
    from apps.data_collection.models import CleanedPriceData

    # 获取60天历史数据
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=60)

    data = CleanedPriceData.objects.filter(
        product_id=product_id,
        date__gte=start_date,
        date__lte=end_date
    ).values('date', 'avg_price').order_by('date')

    daily_prices = {}
    for item in data:
        date = item['date']
        dow = date.weekday()  # 0=周一
        is_weekend = dow >= 5

        if date not in daily_prices:
            daily_prices[date] = {'prices': [], 'is_weekend': is_weekend}
        daily_prices[date]['prices'].append(float(item['avg_price']))

    # 计算周末/工作日效应
    weekend_prices = []
    weekday_prices = []

    for date, info in daily_prices.items():
        avg = np.mean(info['prices'])
        if info['is_weekend']:
            weekend_prices.append(avg)
        else:
            weekday_prices.append(avg)

    weekend_effect = np.mean(weekend_prices) / np.mean(weekday_prices) if weekday_prices else 1.0

    # 简单预测：最近7天均值 * 季节调整
    recent_prices = list(daily_prices.values())[-7:]
    recent_avg = np.mean([np.mean(p['prices']) for p in recent_prices])

    predictions = []
    future_date = end_date + timedelta(days=1)

    for i in range(future_days):
        dow = future_date.weekday()
        is_weekend = dow >= 5

        # 周末效应
        effect = weekend_effect if is_weekend else 1.0

        # 短期趋势
        if i < len(recent_prices):
            trend = np.mean([np.mean(p['prices']) for p in recent_prices[-3:]]) - \
                    np.mean([np.mean(p['prices']) for p in recent_prices[:-3]])
        else:
            trend = 0

        pred = recent_avg * effect + trend * (i + 1) * 0.2
        predictions.append(round(max(0, pred), 2))

        future_date += timedelta(days=1)

    return {
        'success': True,
        'method': 'Seasonal',
        'weekend_effect': round(weekend_effect, 3),
        'recent_avg': round(recent_avg, 2),
        'predictions': predictions
    }


def test_predictions():
    """测试各种预测方法"""
    print('=' * 70)
    print('Price Prediction Methods Comparison')
    print('=' * 70)

    test_products = [14, 18, 13, 12, 21, 17, 6, 22]

    for pid in test_products:
        history = get_product_price_history(pid, days=30)
        if len(history) < 10:
            continue

        hist_mean = np.mean(history)
        hist_std = np.std(history)

        # EMA 预测
        ema_result = predict_with_ema(pid, future_days=7)
        if ema_result['success']:
            ema_mean = np.mean(ema_result['predictions'])
            ema_diff = abs(ema_mean - hist_mean) / hist_mean * 100

        # 季节性预测
        seasonal_result = predict_with_seasonal(pid, future_days=7)
        if seasonal_result['success']:
            seasonal_mean = np.mean(seasonal_result['predictions'])
            seasonal_diff = abs(seasonal_mean - hist_mean) / hist_mean * 100

        try:
            from apps.data_collection.models import AgriculturalProduct
            name = AgriculturalProduct.objects.get(id=pid).name
        except:
            name = f'ID:{pid}'

        print(f'\n{name} (ID:{pid}):')
        print(f'  History: mean={hist_mean:.2f}, std={hist_std:.2f}')
        print(f'  EMA Predictions: {ema_result.get("predictions", [])[:5]}')
        print(f'  EMA Mean: {ema_mean:.2f}, Diff: {ema_diff:.1f}%')
        print(f'  Seasonal Predictions: {seasonal_result.get("predictions", [])[:5]}')
        print(f'  Seasonal Mean: {seasonal_mean:.2f}, Diff: {seasonal_diff:.1f}%')

    print('\n' + '=' * 70)
    print('Recommendation: Use simple EMA or Seasonal method for better accuracy')
    print('=' * 70)


if __name__ == '__main__':
    test_predictions()
