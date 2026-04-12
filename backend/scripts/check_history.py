# -*- coding: utf-8 -*-
import os, sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'configs.settings')
sys.path.insert(0, '.')
import django
django.setup()

from apps.data_analysis.lstm_service import get_product_price_history
from apps.data_collection.models import AgriculturalProduct
from datetime import datetime, timedelta

today = datetime.now().date()
print(f'今天是: {today}')
print(f'90天前是: {today - timedelta(days=90)}')
print()

print('检查每个产品的历史数据:')
products = AgriculturalProduct.objects.filter(is_active=True)[:10]
for p in products:
    # 请求90天历史
    history = get_product_price_history(p.id, days=90)
    print(f'{p.id}: {p.name} - {len(history)}天历史数据')
    if history:
        print(f'  数据: {history[:5]}...{history[-5:]}')
