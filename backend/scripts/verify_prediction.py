# -*- coding: utf-8 -*-
import os
import sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'configs.settings')
sys.path.insert(0, '.')
import django
django.setup()

from apps.data_collection.models import AgriculturalProduct
from apps.data_analysis.lstm_service import predict_product_price

print('=' * 50)
print('验证所有产品的预测能力')
print('=' * 50)

products = AgriculturalProduct.objects.filter(is_active=True)[:20]
success_count = 0
fail_count = 0

for p in products:
    result = predict_product_price(p.id, future_days=7)
    if result.get('success'):
        pred_prices = result.get('prediction', {}).get('prices', [])
        hist_dates = result.get('historical', {}).get('dates', [])
        print(f'{p.id}: {p.name} - 历史{len(hist_dates)}天, 预测{len(pred_prices)}天')
        success_count += 1
    else:
        err = result.get('error', '失败')
        print(f'{p.id}: {p.name} - {err[:40]}')
        fail_count += 1

print('=' * 50)
print(f'总计: {success_count}个成功, {fail_count}个失败')
print('=' * 50)
