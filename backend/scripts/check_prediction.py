# -*- coding: utf-8 -*-
import os
import sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'configs.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import django
django.setup()

from apps.data_analysis.lstm_service import get_product_price_history, predict_product_price
from apps.data_collection.models import AgriculturalProduct

print("=" * 50)
print("检查各产品的预测能力")
print("=" * 50)

products = AgriculturalProduct.objects.filter(is_active=True)[:15]
for p in products:
    history = get_product_price_history(p.id, days=60)
    print(f'{p.id}: {p.name} - {len(history)}天数据')
    
    if len(history) >= 12:
        result = predict_product_price(p.id, future_days=7)
        pred_prices = result.get('prediction', {}).get('prices', [])
        print(f'  预测成功: {result.get("success")}, 预测数据: {len(pred_prices)}天')
        if result.get('success') and pred_prices:
            print(f'  预测价格: {pred_prices[:3]}...')
    else:
        print(f'  数据不足: {len(history)}天 < 12天')
    print()

print("=" * 50)
