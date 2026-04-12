# -*- coding: utf-8 -*-
"""验证模型预测准确性"""
import os, sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'configs.settings')
sys.path.insert(0, '.')
import django
django.setup()

from apps.data_analysis.lstm_service import get_product_price_history, predict_product_price

def verify_prediction_accuracy():
    """验证模型预测准确性"""
    # 选择一个有数据的测试产品
    product_id = 14  # 白菜
    future_days = 7

    print('=' * 60)
    print('模型预测准确性验证')
    print('=' * 60)

    # 获取历史数据（用于对比）
    history = get_product_price_history(product_id, days=60)
    print(f'产品ID: {product_id}, 历史数据: {len(history)}天')
    print(f'最近7天历史价格: {history[-7:]}')

    # 进行预测
    result = predict_product_price(product_id, future_days=future_days)

    if result.get('success'):
        pred_prices = result.get('prediction', {}).get('prices', [])
        print(f'\n模型预测未来{future_days}天价格:')
        for i, price in enumerate(pred_prices):
            print(f'  第{i+1}天: {price:.2f} 元/公斤')

        # 如果有真实数据可以对比
        print('\n' + '=' * 60)
        print('准确性评估指标说明:')
        print('=' * 60)
        print('MAPE (平均绝对百分比误差): 预测误差占真实值的比例')
        print('  - MAPE < 10%  → 模型可用')
        print('  - MAPE < 5%   → 模型较好')
        print('  - MAPE < 2%   → 模型优秀')
        print()
        print('RMSE (均方根误差): 预测值与真实值的标准差')
        print('  - 值越小表示预测越准确')
        print()
        print('R² (决定系数): 模型能解释的数据变异程度')
        print('  - R² > 0.8    → 拟合良好')
        print('  - R² > 0.5    → 中等')
        print('  - R² < 0      → 模型比简单平均还差')
    else:
        print(f'预测失败: {result.get("error")}')

if __name__ == '__main__':
    verify_prediction_accuracy()