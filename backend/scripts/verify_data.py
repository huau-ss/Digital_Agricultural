# -*- coding: utf-8 -*-
import os, sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'configs.settings')
sys.path.insert(0, '.')
import django
django.setup()

from apps.data_collection.models import CleanedPriceData, AgriculturalProduct
from datetime import datetime, timedelta

# 检查最近30天数据
today = datetime.now().date()
thirty_days_ago = today - timedelta(days=30)

print('最近30天有数据的产品:')
from django.db.models import Count
stats = CleanedPriceData.objects.filter(date__gte=thirty_days_ago).values(
    'product__name', 'product_id'
).annotate(
    cnt=Count('id'),
    date_cnt=Count('date', distinct=True)
).order_by('-cnt')[:15]

for s in stats:
    print(f'  {s["product__name"]}(ID:{s["product_id"]}): {s["cnt"]}条, {s["date_cnt"]}天')

print()
print('检查默认产品(第一个有数据的):')
if stats:
    first = stats[0]
    pid = first['product_id']
    pname = first['product__name']
    print(f'产品: {pname} (ID: {pid})')

    # 检查该产品的最近30天数据
    data = CleanedPriceData.objects.filter(
        product_id=pid,
        date__gte=thirty_days_ago
    ).values('date', 'avg_price').order_by('date')

    dates = list(data.values_list('date', flat=True).distinct())
    print(f'最近30天数据: {data.count()}条, {len(dates)}天')
    if dates:
        print(f'日期范围: {dates[0]} ~ {dates[-1]}')
