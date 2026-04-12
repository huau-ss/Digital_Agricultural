# -*- coding: utf-8 -*-
"""深入分析模型预测偏差问题"""
import os, sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'configs.settings')
sys.path.insert(0, '.')
import django
django.setup()

import logging
logging.basicConfig(level=logging.INFO, format='%(message)s')

from apps.data_collection.models import CleanedPriceData
from apps.data_analysis.lstm_service import get_product_price_history, predict_product_price
from datetime import datetime, timedelta
import numpy as np

print('=' * 60)
print('Model Prediction Analysis')
print('=' * 60)

product_id = 14  # Bai Cai

# 1. Check raw data range
data = CleanedPriceData.objects.filter(product_id=product_id).order_by('-date')[:50]
prices = [float(d.avg_price) for d in data]

print('Raw data stats (last 50):')
print('  Min: %.2f' % min(prices))
print('  Max: %.2f' % max(prices))
print('  Mean: %.2f' % np.mean(prices))
print('  Std: %.2f' % np.std(prices))

# 2. Check scaler normalization
import pickle
scaler_path = 'models/lstm/scaler.pkl'
try:
    with open(scaler_path, 'rb') as f:
        scaler = pickle.load(f)
    print('\nScaler params:')
    print('  data_min: %.2f' % scaler.data_min_[0])
    print('  data_max: %.2f' % scaler.data_max_[0])
except Exception as e:
    print('  Read failed: %s' % str(e))

# 3. Prediction test
print('\nPrediction test:')
history = get_product_price_history(product_id, days=30)
print('  History mean: %.2f' % np.mean(history))
print('  History range: %.2f ~ %.2f' % (min(history), max(history)))

result = predict_product_price(product_id, future_days=3)
if result.get('success'):
    pred = result.get('prediction', {}).get('prices', [])
    print('  Prediction: %s' % pred)
else:
    print('  Failed: %s' % result.get('error'))

print('\n' + '=' * 60)
print('Root cause analysis:')
print('=' * 60)
print('Scaler range vs actual data mismatch?')