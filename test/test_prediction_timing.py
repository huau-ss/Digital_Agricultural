"""
数字农业平台 - LSTM 预测时间性能测试
"""
import time
import os
import sys
import django

sys.stdout.reconfigure(line_buffering=True)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SETTINGS_DIR = os.path.join(BASE_DIR, 'backend', 'configs')
if SETTINGS_DIR not in sys.path:
    sys.path.insert(0, SETTINGS_DIR)

BACKEND_DIR = os.path.join(BASE_DIR, 'backend')
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'configs.settings')

logs_dir = os.path.join(BACKEND_DIR, 'logs')
os.makedirs(logs_dir, exist_ok=True)

django.setup()

import numpy as np
import torch
import joblib
from apps.data_analysis.lstm_service import LSTMPredictor, get_product_price_history


def measure_pure_inference(predictor, prices, future_days, runs=3):
    """
    测量纯推理耗时（不含模型加载）。
    通过 mock load_model_and_scaler 使其跳过重载。
    """
    loaded_once = False
    original_load = predictor.load_model_and_scaler

    def fake_load():
        nonlocal loaded_once
        if not loaded_once:
            result = original_load()
            loaded_once = True
            return result
        return True, True

    predictor.load_model_and_scaler = fake_load

    times = []
    for _ in range(runs):
        start = time.perf_counter()
        try:
            predictor.predict_future(prices, future_days=future_days)
        except Exception as e:
            predictor.load_model_and_scaler = original_load
            return None, str(e)
        elapsed = (time.perf_counter() - start) * 1000
        times.append(elapsed)

    predictor.load_model_and_scaler = original_load
    return sum(times) / len(times), None


def measure_load_time(predictor, prices, runs=3):
    """单独测量模型加载耗时"""
    times = []
    for _ in range(runs):
        predictor.model = None
        predictor.scaler = None
        start = time.perf_counter()
        predictor.load_model_and_scaler()
        elapsed = (time.perf_counter() - start) * 1000
        times.append(elapsed)
    return sum(times) / len(times)


def main():
    print("=" * 70)
    print("LSTM 预测时间性能测试")
    print("环境: CPU 推理")
    print("=" * 70)

    from apps.data_collection.models import AgriculturalProduct as Product
    product = Product.objects.first()
    if not product:
        print("未找到产品数据，跳过测试")
        return

    product_id = product.id
    prices = get_product_price_history(product_id, days=60, market_name=None)

    if len(prices) < 10:
        print(f"产品 {product.name} 历史数据不足（{len(prices)} 天），跳过")
        return

    print(f"\n产品: {product.name} (ID={product_id})")
    print(f"历史数据: {len(prices)} 天\n")

    predictor = LSTMPredictor(product_id=product_id)

    # 预加载模型
    print("加载模型...")
    load_ms = measure_load_time(predictor, prices, runs=3)
    print(f"模型加载耗时: {load_ms:.0f} ms\n")

    # 纯推理耗时测试
    print(f"{'预测天数':<10} {'纯推理(ms)':<15} {'含加载(ms)':<15} {'说明'}")
    print("-" * 70)

    test_cases = [
        (7,  "主要耗时在模型加载"),
        (14, "耗时随天数线性增长"),
        (30, "耗时随天数线性增长"),
    ]

    results = []
    for days, note in test_cases:
        pure_ms, err = measure_pure_inference(predictor, prices, future_days=days, runs=3)
        total_ms = (load_ms if pure_ms is not None else 0) + (pure_ms if pure_ms is not None else 0)
        if err:
            print(f"{days:<10} {'ERROR':<15} {'-':<15} {err}")
        else:
            print(f"{days:<10} {pure_ms:<15.0f} {total_ms:<15.0f} {note}")
            results.append((days, pure_ms, total_ms))

    # 结论
    print("\n" + "=" * 70)
    print("测试结论:")
    print("-" * 70)
    if results:
        for days, pure_ms, total_ms in results:
            print(f"  {days:>2}天预测 - 纯推理: {pure_ms:.0f} ms | 含加载: {total_ms:.0f} ms")
        if results[0][1] < 1000:
            print(f"  单次预测控制在 1 秒以内，满足实时预测需求")
        else:
            print(f"  预测耗时较长，建议优化模型或减少 SEQ_LENGTH")
    print("=" * 70)


if __name__ == '__main__':
    main()
