# -*- coding: utf-8 -*-
import os, sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'configs.settings')
sys.path.insert(0, '.')
import django
django.setup()

from apps.data_collection.models import CleanedPriceData
from datetime import datetime, timedelta

product_id = 29
end_date = datetime.now().date()
start_date = end_date - timedelta(days=90)

print(f'查询范围: {start_date} ~ {end_date}')
print()

data = CleanedPriceData.objects.filter(
    product_id=product_id,
    date__gte=start_date,
    date__lte=end_date
).values('date', 'avg_price').order_by('date')

print(f'香蕉(29)的原始数据:')
dates = {}
for item in data:
    ds = item['date'].strftime('%Y-%m-%d')
    if ds not in dates:
        dates[ds] = []
    dates[ds].append(float(item['avg_price']))

print(f'共 {len(data)} 条记录, {len(dates)} 个不同日期')
print('日期列表:')
for ds in sorted(dates.keys())[:20]:
    avg = sum(dates[ds]) / len(dates[ds])
    print(f'  {ds}: {len(dates[ds])}条, 平均={avg:.2f}')
