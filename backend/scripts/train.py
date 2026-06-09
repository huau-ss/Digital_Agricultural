# -*- coding: utf-8 -*-
"""
LSTM 模型离线训练脚本
训练前会先从数据库读取所有农产品的历史价格数据，
训练完成后生成 .pth 模型文件，供 API 直接加载进行推理。

使用方法：
  cd backend
  python -m scripts.train
"""
import os
import sys
import django

# 配置 Django 环境
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
backend_dir = os.path.join(BASE_DIR, 'backend')
sys.path.insert(0, backend_dir)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'configs.settings')
django.setup()

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
from sklearn.preprocessing import MinMaxScaler
from datetime import datetime, timedelta

from apps.data_analysis.lstm_service import LSTMModel, MODEL_DIR
from apps.data_collection.models import CleanedPriceData


def get_all_products_price_data(min_days=30):
    """
    获取所有产品的历史价格数据
    返回: {product_id: [prices]}
    """
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=90)

    print(f"正在获取 {start_date} 至 {end_date} 的数据...")

    # 查询所有数据
    price_data = CleanedPriceData.objects.filter(
        date__gte=start_date,
        date__lte=end_date
    ).values('product_id', 'date', 'avg_price').order_by('product_id', 'date')

    # 按产品分组
    product_prices = {}
    for item in price_data:
        pid = item['product_id']
        date_str = item['date'].strftime('%Y-%m-%d')
        if pid not in product_prices:
            product_prices[pid] = {}
        if date_str not in product_prices[pid]:
            product_prices[pid][date_str] = []
        product_prices[pid][date_str].append(float(item['avg_price']))

    # 计算每日平均价格，过滤数据不足的产品
    result = {}
    for pid, daily_data in product_prices.items():
        prices = []
        for date_str in sorted(daily_data.keys()):
            avg_price = sum(daily_data[date_str]) / len(daily_data[date_str])
            prices.append(round(avg_price, 2))

        if len(prices) >= min_days:
            result[pid] = prices

    print(f"共有 {len(result)} 个产品数据充足（>= {min_days} 天）可用于训练")
    return result


def create_sliding_windows(data, seq_length):
    """创建滑动窗口数据集"""
    X, y = [], []
    for i in range(len(data) - seq_length):
        X.append(data[i:i + seq_length])
        y.append(data[i + seq_length])
    return np.array(X), np.array(y)


def train_model(product_id, prices, seq_length=10, epochs=50, batch_size=32, lr=0.001):
    """
    训练单个产品的 LSTM 模型
    """
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    # 归一化
    scaler = MinMaxScaler(feature_range=(0, 1))
    prices_array = np.array(prices).reshape(-1, 1)
    scaled_data = scaler.fit_transform(prices_array).flatten()

    # 创建数据集
    X, y = create_sliding_windows(scaled_data, seq_length)
    X = torch.FloatTensor(X).unsqueeze(-1)  # (samples, seq_len, 1)
    y = torch.FloatTensor(y).unsqueeze(-1)

    dataset = TensorDataset(X, y)
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

    # 初始化模型
    model = LSTMModel(input_size=1, hidden_size=64, num_layers=2, output_size=1, dropout=0.2)
    model = model.to(device)

    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)

    # 训练
    model.train()
    for epoch in range(epochs):
        total_loss = 0
        for batch_X, batch_y in dataloader:
            batch_X = batch_X.to(device)
            batch_y = batch_y.to(device)

            optimizer.zero_grad()
            outputs = model(batch_X)
            loss = criterion(outputs, batch_y)
            loss.backward()
            optimizer.step()

            total_loss += loss.item()

        if (epoch + 1) % 10 == 0:
            avg_loss = total_loss / len(dataloader)
            print(f"  Epoch {epoch + 1}/{epochs}, Loss: {avg_loss:.6f}")

    return model, scaler


def train_all_products():
    """
    训练所有产品通用模型
    将所有产品的数据合并训练一个通用模型
    """
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"使用设备: {device}")

    # 获取所有产品数据
    product_data = get_all_products_price_data(min_days=30)
    if not product_data:
        print("没有足够的数据用于训练")
        return

    # 合并所有数据
    all_prices = []
    for prices in product_data.values():
        all_prices.extend(prices)

    print(f"总训练样本数: {len(all_prices)}")

    # 归一化
    scaler = MinMaxScaler(feature_range=(0, 1))
    all_prices = np.array(all_prices).reshape(-1, 1)
    scaled_data = scaler.fit_transform(all_prices).flatten()

    # 创建数据集
    seq_length = 10
    X, y = create_sliding_windows(scaled_data, seq_length)
    X = torch.FloatTensor(X).unsqueeze(-1)
    y = torch.FloatTensor(y).unsqueeze(-1)

    dataset = TensorDataset(X, y)
    dataloader = DataLoader(dataset, batch_size=64, shuffle=True)

    # 初始化模型
    model = LSTMModel(input_size=1, hidden_size=64, num_layers=2, output_size=1, dropout=0.2)
    model = model.to(device)

    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

    # 训练
    epochs = 100
    model.train()
    print(f"\n开始训练通用 LSTM 模型...")
    for epoch in range(epochs):
        total_loss = 0
        for batch_X, batch_y in dataloader:
            batch_X = batch_X.to(device)
            batch_y = batch_y.to(device)

            optimizer.zero_grad()
            outputs = model(batch_X)
            loss = criterion(outputs, batch_y)
            loss.backward()
            optimizer.step()

            total_loss += loss.item()

        if (epoch + 1) % 20 == 0:
            avg_loss = total_loss / len(dataloader)
            print(f"Epoch {epoch + 1}/{epochs}, Loss: {avg_loss:.6f}")

    # 保存模型
    model_path = os.path.join(MODEL_DIR, 'lstm_general.pth')
    torch.save(model.state_dict(), model_path)
    print(f"\n通用模型已保存: {model_path}")

    return model


def main():
    """主训练流程"""
    print("=" * 50)
    print("LSTM 模型离线训练")
    print("=" * 50)

    # 创建模型保存目录
    os.makedirs(MODEL_DIR, exist_ok=True)

    # 训练通用模型
    train_all_products()

    print("\n训练完成！模型文件已保存到:")
    print(f"  {MODEL_DIR}")
    print("\nAPI 调用时会自动加载模型进行推理。")


if __name__ == '__main__':
    main()
