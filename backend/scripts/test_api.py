# -*- coding: utf-8 -*-
import urllib.request
import json

url = 'http://127.0.0.1:8000/api/data-collection/visualization/'
try:
    with urllib.request.urlopen(url, timeout=5) as response:
        data = json.loads(response.read().decode('utf-8'))
        print('Status: 200 OK')
        print('Products count:', len(data))
        if data:
            print('First product:', data[0])
except urllib.error.URLError as e:
    print('Error:', e)
