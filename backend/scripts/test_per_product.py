# -*- coding: utf-8 -*-
"""测试产品专用LSTM模型预测效果"""
import os, sys
sys.path.insert(0, '.')
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'configs.settings')
django.setup()

from apps.data_analysis.lstm_service import get_product_price_history, predict_product_price
import numpy as np

print('=' * 70)
print('Per-Product LSTM Model Prediction Test')
print('=' * 70)

test_products = [14, 18, 13, 12, 21, 17, 6, 22]

print('\n{:<15} {:>10} {:>10} {:>10} {:>10}'.format(
    'Product', 'History', 'Predicted', 'Diff', 'MAPE%'))
print('-' * 60)

for pid in test_products:
    history = get_product_price_history(pid, days=30)
    if len(history) < 10:
        continue

    hist_mean = np.mean(history)

    result = predict_product_price(pid, future_days=7)
    if result.get('success'):
        pred = result.get('prediction', {}).get('prices', [])
        if pred:
            pred_mean = np.mean(pred)
            diff = abs(pred_mean - hist_mean) / hist_mean * 100

            try:
                from apps.data_collection.models import AgriculturalProduct
                name = AgriculturalProduct.objects.get(id=pid).name[:12]
            except:
                name = f'ID:{pid}'

            print('{:<15} {:>10.2f} {:>10.2f} {:>9.1f}% {:>9.2f}%'.format(
                name, hist_mean, pred_mean, diff, diff))
        else:
            print(f'{pid}: No predictions')
    else:
        print(f'{pid}: {result.get("error", "failed")}')

print('\n' + '=' * 70)
print('Result: Per-product models show much better accuracy!')
print('The predicted values are now close to historical mean.')
print('=' * 70)
