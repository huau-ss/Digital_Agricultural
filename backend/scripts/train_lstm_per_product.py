# -*- coding: utf-8 -*-
"""
LSTM 价格预测模型 - 产品专用版本
为每个产品单独训练模型，提高预测准确性
"""
import os, sys, warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import joblib, pymysql
from datetime import datetime, timedelta

# ==================== 配置参数 ====================
DB = {
    'host': 'localhost', 'port': 3306, 'user': 'root',
    'password': '123456', 'database': 'digital_agriculture', 'charset': 'utf8mb4'
}

MDIR = r'E:\PyCharm 2025.2.1.1\pythonProjects\Digital Agriculture\backend\models\lstm_per_product'
os.makedirs(MDIR, exist_ok=True)

# 训练超参数
SEQ_LENGTH = 7          # 序列长度 （每次训练的输入长度）
HIDDEN_SIZE = 64        # 隐藏层大小（每次训练的隐藏层大小）
NUM_LAYERS = 2         # 层数（每次训练的层数）
DROPOUT = 0.2          #  丢弃率（每次训练的丢弃率）
LEARNING_RATE = 0.001  # 学习率 （每次训练的步长）
EPOCHS = 100           # 训练轮数（每次训练的完整数据集数）
BATCH_SIZE = 16        # 批量大小   （每次训练的样本数）
MIN_DATA_POINTS = 30   # 最少数据点数（至少需要30天数据）


# ==================== LSTM 模型 ====================
class PriceLSTM(nn.Module):             # 继承PyTorch的神经网络基类
    def __init__(self, input_size=1, hidden_size=64, num_layers=2, dropout=0.2):
        super().__init__()
        self.lstm = nn.LSTM(
            input_size=input_size,   # 输入大小（1个特征）
            hidden_size=hidden_size, # 64个神经元
            num_layers=num_layers,  # 层数
            batch_first=True,      # 是否批量第一
            dropout=dropout)       # 丢弃率
        self.fc = nn.Linear(hidden_size, 1)  # 全连接层（把64个神经元压缩成1个输出（预测价格））

    # 前向传播（机器人思考）
    def forward(self, x):
        lstm_out, _ = self.lstm(x)
        return self.fc(lstm_out[:, -1, :])  # 取最后一个时间步的输出（预测价格）


def load_product_data(product_id, days=120):
    """加载指定产品的数据"""
    conn = pymysql.connect(**DB)
    try:
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)

        with conn.cursor() as cursor:
            cursor.execute(
                """SELECT date, AVG(avg_price) as price
                   FROM cleaned_price_data
                   WHERE product_id=%s AND date>=%s AND date<=%s AND is_outlier=0
                   GROUP BY date ORDER BY date""",
                (product_id, start_date, end_date)
            )
            rows = cursor.fetchall()
    finally:
        conn.close()

    if not rows:
        return None

    df = pd.DataFrame(rows, columns=['date', 'price'])
    df = df.sort_values('date').reset_index(drop=True)
    return df


def create_sequences(data, seq_length):
    """创建滑动窗口序列"""
    X, Y = [], []
    for i in range(len(data) - seq_length):
        X.append(data[i:i + seq_length])
        Y.append(data[i + seq_length])
    return np.array(X, dtype=np.float32), np.array(Y, dtype=np.float32)


def train_single_product(product_id, product_name):
    """训练单个产品的模型"""
    print(f'\n{"="*50}')
    print(f'Training model for: {product_name} (ID: {product_id})')
    print('=' * 50)

    # 加载数据
    df = load_product_data(product_id)
    if df is None or len(df) < MIN_DATA_POINTS:
        print(f'  Skip: Not enough data ({len(df) if df is not None else 0} points)')
        return None

    prices = df['price'].values
    print(f'  Data: {len(prices)} points, range {prices.min():.2f} ~ {prices.max():.2f}')

    # 归一化（基于该产品自身数据）
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled_prices = scaler.fit_transform(prices.reshape(-1, 1)).flatten()

    # 创建序列
    X, Y = create_sequences(scaled_prices, SEQ_LENGTH)
    print(f'  Sequences: X={X.shape}, Y={Y.shape}')

    # 划分训练/测试集
    train_size = int(len(X) * 0.8)
    if train_size < 10:
        print(f'  Skip: Too few training samples')
        return None

    X_train = torch.FloatTensor(X[:train_size]).reshape(-1, SEQ_LENGTH, 1)          # 训练集输入
    Y_train = torch.FloatTensor(Y[:train_size]).reshape(-1, 1)                      # 训练集输出
    X_test = torch.FloatTensor(X[train_size:]).reshape(-1, SEQ_LENGTH, 1)           # 测试集输入
    Y_test = torch.FloatTensor(Y[train_size:]).reshape(-1, 1)                       # 测试集输出

    # DataLoader
    train_loader = DataLoader(TensorDataset(X_train, Y_train), batch_size=BATCH_SIZE, shuffle=True)  # 数据加载器（批量读取数据）

    # 模型
    device = torch.device('cpu')
    model = PriceLSTM(
        input_size=1, 
        hidden_size=HIDDEN_SIZE, 
        num_layers=NUM_LAYERS, 
        dropout=DROPOUT
        ).to(device)

    criterion = nn.MSELoss()  # 均方误差损失函数
    optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)  # 优化器（Adam优化算法）    

    # 训练
    for epoch in range(EPOCHS):
        model.train()
        for X_batch, Y_batch in train_loader:
            X_batch, Y_batch = X_batch.to(device), Y_batch.to(device)
            optimizer.zero_grad()         # 清零梯度
            pred = model(X_batch)         # 预测
            loss = criterion(pred, Y_batch) # 损失
            loss.backward()                 # 反向传播
            optimizer.step()                # 更新参数  

    # 评估
    model.eval()
    with torch.no_grad():       # 不计算梯度
        pred_test = model(X_test.to(device)).cpu().numpy().flatten()  # 用测试集预测
        Y_test_orig = scaler.inverse_transform(Y_test.reshape(-1, 1)).flatten()  # 转回原始价格
        pred_test_orig = scaler.inverse_transform(pred_test.reshape(-1, 1)).flatten()  # 预测值

    # 计算评估指标
    rmse = float(np.sqrt(mean_squared_error(Y_test_orig, pred_test_orig)))
    mae = float(mean_absolute_error(Y_test_orig, pred_test_orig))
    r2 = float(r2_score(Y_test_orig, pred_test_orig))
    mape = float(np.mean(np.abs((Y_test_orig - pred_test_orig) / np.where(Y_test_orig == 0, 1, Y_test_orig))) * 100)

    # 保存模型和scaler
    model_path = os.path.join(MDIR, f'lstm_p{product_id}.pth')
    scaler_path = os.path.join(MDIR, f'scaler_p{product_id}.pkl')

    torch.save(model.state_dict(), model_path)
    joblib.dump(scaler, scaler_path)

    return {
        'product_id': product_id,
        'product_name': product_name,
        'data_points': len(prices),
        'rmse': rmse,
        'mae': mae,
        'r2': r2,
        'mape': mape,
        'price_range': (float(prices.min()), float(prices.max()))
    }


def main():
    print('=' * 60)
    print('LSTM Per-Product Model Training')
    print('=' * 60)

    # 获取所有有数据的产品
    conn = pymysql.connect(**DB)
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """SELECT p.id, p.name, COUNT(c.id) as cnt
                   FROM agricultural_products p
                   JOIN cleaned_price_data c ON p.id = c.product_id
                   WHERE c.date >= DATE_SUB(CURDATE(), INTERVAL 120 DAY) AND c.is_outlier = 0
                   GROUP BY p.id, p.name
                   HAVING cnt >= %s
                   ORDER BY cnt DESC""",
                (MIN_DATA_POINTS,)
            )
            products = cursor.fetchall()
    finally:
        conn.close()

    print(f'\nFound {len(products)} products with enough data')
    print('=' * 60)

    # 为每个产品训练模型
    results = []
    for prod_id, prod_name, cnt in products:
        try:
            result = train_single_product(prod_id, prod_name)
            if result:
                results.append(result)
        except Exception as e:
            print(f'  Error: {e}')

    # 汇总
    print('\n' + '=' * 60)
    print('Training Summary')
    print('=' * 60)
    print(f'Total products trained: {len(results)}')
    print(f'\n{"Product":<20} {"Data":>6} {"RMSE":>8} {"MAE":>8} {"R2":>8} {"MAPE":>8}')
    print('-' * 60)

    for r in sorted(results, key=lambda x: x['mape']):
        print(f'{r["product_name"][:18]:<20} {r["data_points"]:>6} {r["rmse"]:>8.4f} {r["mae"]:>8.4f} {r["r2"]:>8.4f} {r["mape"]:>7.2f}%')

    # 保存模型列表
    model_list = {r['product_id']: r for r in results}
    joblib.dump(model_list, os.path.join(MDIR, 'model_registry.pkl'))

    print('\n' + '=' * 60)
    print(f'Models saved to: {MDIR}')
    print('=' * 60)


if __name__ == '__main__':
    main()
