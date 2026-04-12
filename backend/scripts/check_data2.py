# -*- coding: utf-8 -*-
import os, sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'configs.settings')
sys.path.insert(0, '.')
import django
django.setup()

from apps.data_collection.models import CleanedPriceData
from django.db.models import Count

# 按产品统计每个产品有多少个不同日期
product_dates = CleanedPriceData.objects.values('product__name').annotate(
    product_count=Count('id'),
    date_count=Count('date', distinct=True)
).order_by('-product_count')[:20]

print('各产品数据统计:')
print('产品名称              | 日期数 | 记录数')
print('-' * 40)
for s in product_dates:
    name = s['product__name']
    dc = s['date_count']
    pc = s['product_count']
    print(f'{name:20s} | {dc:6d} | {pc:6d}')
