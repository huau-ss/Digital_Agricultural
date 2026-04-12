# -*- coding: utf-8 -*-
import os, sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'configs.settings')
sys.path.insert(0, '.')
import django
django.setup()

from apps.data_collection.models import CleanedPriceData, AgriculturalProduct
from datetime import datetime, timedelta

product = AgriculturalProduct.objects.get(id=73)
print(f'产品: {product.name} (ID: {product.id})')

# 检查清洗后数据
data = CleanedPriceData.objects.filter(product_id=73)
print(f'清洗后数据总数: {data.count()}')

dates = list(data.values_list('date', flat=True).distinct().order_by('date'))
if dates:
    print(f'数据日期范围: {dates[0]} 到 {dates[-1]}')
    print(f'共 {len(dates)} 个日期')
else:
    print('没有清洗后数据')

# 检查最近30天数据
today = datetime.now().date()
thirty_days_ago = today - timedelta(days=30)
recent = data.filter(date__gte=thirty_days_ago)
recent_dates = list(recent.values_list('date', flat=True).distinct().order_by('date'))
print(f'\n最近30天数据: {recent.count()}条, {len(recent_dates)}个日期')
if recent_dates:
    print(f'  从 {recent_dates[0]} 到 {recent_dates[-1]}')

print()
print('检查有数据的产品(前15):')
from django.db.models import Count
stats = CleanedPriceData.objects.filter(date__gte=thirty_days_ago).values('product__name').annotate(
    cnt=Count('id'),
    date_cnt=Count('date', distinct=True)
).order_by('-cnt')[:15]
for s in stats:
    print(f'  {s["product__name"]}: {s["cnt"]}条, {s["date_cnt"]}天')
