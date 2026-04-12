# -*- coding: utf-8 -*-
import urllib.request
import json

base_url = 'http://127.0.0.1:8000/api/data-collection/visualization/'

endpoints = [
    ('products', ''),
    ('price_trend', '?product_id=1&days=30'),
    ('province_heatmap', '?product_id=1'),
    ('region_comparison', '?product_id=1'),
]

for name, params in endpoints:
    url = base_url + name + '/' + params
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            print(f'{name}: OK')
            if isinstance(data, dict):
                keys = list(data.keys())[:5]
                print(f'  Keys: {keys}')
            elif isinstance(data, list):
                print(f'  Length: {len(data)}')
    except Exception as e:
        print(f'{name}: Error - {e}')
