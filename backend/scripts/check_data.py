# -*- coding: utf-8 -*-
import os, sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'configs.settings')
sys.path.insert(0, '.')
import django
django.setup()

from apps.data_collection.models import CleanedPriceData
from django.db.models import Count

# 按产品统计
stats = CleanedPriceData.objects.values('product__name').annotate(count=Count('id')).order_by('-count')[:15]
print('各产品数据量:')
for s in stats:
    name = s['product__name']
    cnt = s['count']
    print(f'  {name}: {cnt}条')

# 检查时间范围
dates = CleanedPriceData.objects.values_list('date', flat=True).distinct().order_by('date')
dates_list = list(dates)
if dates_list:
    print(f'\n数据时间范围: {dates_list[0]} ~ {dates_list[-1]}')
    print(f'共 {len(dates_list)} 个日期')
