# -*- coding: utf-8 -*-
"""
LSTM 价格预测模型 - 增强版
包含时间特征：月份、季节、星期、节假日
"""
import os, sys
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
import matplotlib
matplotlib.use('Agg')  # 非交互式后端
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import joblib, pymysql
from datetime import datetime, timedelta
import calendar

# ==================== 配置参数 ====================
DB = {
    'host': 'localhost', 'port': 3306, 'user': 'root',
    'password': '123456', 'database': 'digital_agriculture', 'charset': 'utf8mb4'
}

MDIR = r'E:\PyCharm 2025.2.1.1\pythonProjects\Digital Agriculture\backend\models\lstm_enhanced'
os.makedirs(MDIR, exist_ok=True)

# 训练超参数
SEQ_LENGTH = 7       # 滑动窗口长度（天数）
HIDDEN_SIZE = 64     # LSTM 隐藏层维度
NUM_LAYERS = 2       # LSTM 层数
DROPOUT = 0.2        # Dropout
LEARNING_RATE = 0.001
BATCH_SIZE = 16
EPOCHS = 100         # 训练轮数
TRAIN_RATIO = 0.8   # 训练集比例


# ==================== 节假日数据 ====================
HOLIDAYS = {
    (1, 1): 'new_year',
    (1, 21): 'spring_festival', (1, 22): 'spring_festival', (1, 23): 'spring_festival',
    (1, 24): 'spring_festival', (1, 25): 'spring_festival', (1, 26): 'spring_festival',
    (1, 27): 'spring_festival', (1, 28): 'spring_festival', (1, 29): 'spring_festival',
    (1, 30): 'spring_festival', (1, 31): 'spring_festival',
    (2, 1): 'spring_festival', (2, 2): 'spring_festival', (2, 3): 'spring_festival',
    (2, 4): 'spring_festival', (2, 5): 'spring_festival', (2, 6): 'spring_festival',
    (2, 7): 'spring_festival', (2, 8): 'spring_festival', (2, 9): 'spring_festival',
    (2, 10): 'spring_festival', (2, 11): 'spring_festival', (2, 12): 'spring_festival',
    (2, 13): 'spring_festival', (2, 14): 'spring_festival', (2, 15): 'spring_festival',
    (2, 16): 'spring_festival', (2, 17): 'spring_festival', (2, 18): 'spring_festival',
    (2, 19): 'spring_festival', (2, 20): 'spring_festival',
    (4, 4): 'qingming', (4, 5): 'qingming', (4, 6): 'qingming',
    (5, 1): 'labor_day', (5, 2): 'labor_day', (5, 3): 'labor_day',
    (5, 28): 'dragon_boat', (5, 29): 'dragon_boat', (5, 30): 'dragon_boat',
    (9, 15): 'mid_autumn', (9, 16): 'mid_autumn', (9, 17): 'mid_autumn',
    (10, 1): 'national_day', (10, 2): 'national_day', (10, 3): 'national_day',
    (10, 4): 'national_day', (10, 5): 'national_day', (10, 6): 'national_day',
    (10, 7): 'national_day', (10, 8): 'national_day',
}


def get_season(month):
    if month in [3, 4, 5]: return 0
    elif month in [6, 7, 8]: return 1
    elif month in [9, 10, 11]: return 2
    else: return 3


def get_date_features(date):
    month = date.month
    day = date.day
    day_of_week = date.weekday()
    is_weekend = 1 if day_of_week >= 5 else 0
    season = get_season(month)
    month_norm = month / 12.0
    day_of_month_norm = day / 31.0
    day_of_week_norm = day_of_week / 6.0
    is_holiday = 1 if (month, day) in HOLIDAYS else 0

    prev_days = 0
    for i in range(1, 4):
        if (month, day - i) in HOLIDAYS:
            prev_days = 1
            break

    post_days = 0
    for i in range(1, 4):
        if (month, day + i) in HOLIDAYS:
            post_days = 1
            break

    return [month_norm, day_of_week_norm, season, is_weekend, is_holiday, prev_days, post_days]


def load_data(days=365):
    conn = pymysql.connect(**DB)
    try:
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT date, avg_price FROM cleaned_price_data "
                "WHERE date>=%s AND date<=%s AND is_outlier=0 ORDER BY date ASC",
                (start_date, end_date)
            )
            rows = cursor.fetchall()
        df = pd.DataFrame(rows, columns=['date', 'avg_price'])
    finally:
        conn.close()

    df = df.groupby('date')['avg_price'].mean().reset_index()
    df = df.sort_values('date').reset_index(drop=True)

    # 添加日期特征
    df['date'] = pd.to_datetime(df['date'])
    df['features'] = df['date'].apply(lambda x: get_date_features(x.date()))

    feature_cols = ['month_norm', 'day_of_week_norm', 'season', 'is_weekend', 'is_holiday', 'pre_holiday', 'post_holiday']
    features_df = pd.DataFrame(df['features'].tolist(), columns=feature_cols)
    df = pd.concat([df, features_df], axis=1)

    return df


def create_sequences_with_features(df, seq_length):
    prices = df['avg_price'].values
    feature_cols = ['month_norm', 'day_of_week_norm', 'season', 'is_weekend', 'is_holiday', 'pre_holiday', 'post_holiday']
    features = df[feature_cols].values

    X_price, X_features, Y = [], [], []
    for i in range(len(df) - seq_length):
        # 价格序列特征 (seq_length, 1) -> reshape to (seq_length, 1)
        X_price.append(prices[i:i + seq_length].reshape(-1, 1))
        # 日期特征（取序列最后一个日期的特征）(n_features,)
        X_features.append(features[i + seq_length - 1])
        Y.append(prices[i + seq_length])

    return np.array(X_price, dtype=np.float32), np.array(X_features, dtype=np.float32), np.array(Y, dtype=np.float32)


def prepare_dataloaders(X_price, X_features, Y, train_ratio=0.8, batch_size=32):
    train_size = int(len(X_price) * train_ratio)

    train_loader = DataLoader(
        TensorDataset(
            torch.FloatTensor(X_price[:train_size]),
            torch.FloatTensor(X_features[:train_size]),
            torch.FloatTensor(Y[:train_size])
        ),
        batch_size=batch_size, shuffle=True
    )
    test_loader = DataLoader(
        TensorDataset(
            torch.FloatTensor(X_price[train_size:]),
            torch.FloatTensor(X_features[train_size:]),
            torch.FloatTensor(Y[train_size:])
        ),
        batch_size=batch_size, shuffle=False
    )

    return train_loader, test_loader, train_size


class EnhancedLSTM(nn.Module):
    def __init__(self, input_size=1, hidden_size=64, num_layers=2, dropout=0.2, n_features=7):
        super().__init__()
        self.lstm = nn.LSTM(input_size=input_size, hidden_size=hidden_size,
                           num_layers=num_layers, batch_first=True, dropout=dropout)
        self.feature_fc = nn.Sequential(nn.Linear(n_features, 16), nn.ReLU(), nn.Dropout(0.2))
        self.fc = nn.Sequential(nn.Linear(hidden_size + 16, 32), nn.ReLU(), nn.Dropout(0.2), nn.Linear(32, 1))

    def forward(self, x_price, x_features):
        lstm_out, _ = self.lstm(x_price)
        lstm_out = lstm_out[:, -1, :]
        feat_out = self.feature_fc(x_features)
        combined = torch.cat([lstm_out, feat_out], dim=1)
        return self.fc(combined)


def train_model(train_loader, test_loader, X_price_test, X_features_test, Y_test):
    device = torch.device('cpu')
    print(f'Device: {device}')

    model = EnhancedLSTM(input_size=1, hidden_size=HIDDEN_SIZE, num_layers=NUM_LAYERS,
                        dropout=DROPOUT, n_features=7).to(device)

    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, 'min', patience=10, factor=0.5)

    train_losses, test_losses = [], []

    for epoch in range(EPOCHS):
        model.train()
        train_loss = 0
        for X_p, X_f, y in train_loader:
            X_p, X_f, y = X_p.to(device), X_f.to(device), y.to(device)
            optimizer.zero_grad()
            pred = model(X_p, X_f)
            loss = criterion(pred.squeeze(), y)
            loss.backward()
            optimizer.step()
            train_loss += loss.item()

        train_loss /= len(train_loader)
        train_losses.append(train_loss)

        model.eval()
        with torch.no_grad():
            test_pred = model(torch.FloatTensor(X_price_test), torch.FloatTensor(X_features_test))
            test_loss = criterion(test_pred.squeeze(), torch.FloatTensor(Y_test))
            test_losses.append(test_loss.item())

        scheduler.step(test_loss)

        if (epoch + 1) % 10 == 0:
            print(f'Epoch [{epoch+1:3d}/{EPOCHS}] Train: {train_loss:.6f} | Test: {test_loss:.6f}')

    return model, train_losses, test_losses, device


def evaluate_model(model, X_price_test, X_features_test, Y_test, device, scaler):
    model.eval()
    with torch.no_grad():
        predictions = model(torch.FloatTensor(X_price_test), torch.FloatTensor(X_features_test)).numpy().flatten()

    predictions_original = scaler.inverse_transform(predictions.reshape(-1, 1)).flatten()
    Y_original = scaler.inverse_transform(Y_test.reshape(-1, 1)).flatten()

    mse = mean_squared_error(Y_original, predictions_original)
    rmse = np.sqrt(mse)
    mae = mean_absolute_error(Y_original, predictions_original)
    r2 = r2_score(Y_original, predictions_original)

    mask = Y_original > 0.01
    mape = np.mean(np.abs((Y_original[mask] - predictions_original[mask]) / Y_original[mask])) * 100

    print('\n' + '=' * 50)
    print('Model Evaluation Results:')
    print(f'  MSE:   {mse:.4f}')
    print(f'  RMSE:  {rmse:.4f}')
    print(f'  MAE:   {mae:.4f}')
    print(f'  R2:    {r2:.4f}')
    print(f'  MAPE:  {mape:.2f}%')

    return mse, rmse, mae, r2, mape


def plot_training_history(train_losses, test_losses):
    plt.figure(figsize=(10, 5))
    plt.plot(train_losses, label='Train Loss')
    plt.plot(test_losses, label='Test Loss')
    plt.xlabel('Epoch')
    plt.ylabel('Loss (MSE)')
    plt.title('Training History')
    plt.legend()
    plt.grid(True)
    plt.savefig(os.path.join(MDIR, 'training_loss_curve.png'), dpi=150, bbox_inches='tight')
    plt.close()
    print('Loss curve saved!')


if __name__ == '__main__':
    print('=' * 60)
    print('Enhanced LSTM Price Prediction - With Time Features')
    print('=' * 60)

    # 1. 加载数据
    print('\n[1] Loading data...')
    df = load_data(days=120)
    print(f'Data range: {df["date"].min().date()} ~ {df["date"].max().date()}')
    print(f'Total records: {len(df)}')

    # 2. 归一化价格
    scaler = MinMaxScaler(feature_range=(0, 1))
    df['price_scaled'] = scaler.fit_transform(df[['avg_price']])

    # 3. 创建序列
    print('\n[2] Creating sequences...')
    X_price, X_features, Y = create_sequences_with_features(df, SEQ_LENGTH)
    print(f'X_price shape: {X_price.shape}, X_features: {X_features.shape}, Y: {Y.shape}')

    # 4. 准备 DataLoader
    print('\n[3] Preparing dataloaders...')
    train_loader, test_loader, train_size = prepare_dataloaders(X_price, X_features, Y, TRAIN_RATIO, BATCH_SIZE)
    print(f'Samples: {len(X_price)}, Train: {train_size}, Test: {len(X_price) - train_size}')

    # 5. 训练
    print('\n[4] Training Enhanced LSTM...')
    model, train_losses, test_losses, device = train_model(
        train_loader, test_loader,
        X_price[train_size:], X_features[train_size:], Y[train_size:]
    )

    # 6. 评估
    print('\n[5] Evaluating model...')
    evaluate_model(model, X_price[train_size:], X_features[train_size:], Y[train_size:], device, scaler)

    # 7. 保存
    print('\n[6] Saving model...')
    torch.save(model.state_dict(), os.path.join(MDIR, 'enhanced_lstm_model.pth'))
    joblib.dump(scaler, os.path.join(MDIR, 'enhanced_scaler.pkl'))

    config = {'SEQ_LENGTH': SEQ_LENGTH, 'HIDDEN_SIZE': HIDDEN_SIZE, 'NUM_LAYERS': NUM_LAYERS,
              'N_FEATURES': 7, 'TRAIN_RATIO': TRAIN_RATIO}
    joblib.dump(config, os.path.join(MDIR, 'config.pkl'))

    # 8. 训练曲线
    plot_training_history(train_losses, test_losses)

    print('\n' + '=' * 50)
    print('Training Complete!')
    print(f'Model: {MDIR}/enhanced_lstm_model.pth')
    print(f'Scaler: {MDIR}/enhanced_scaler.pkl')
    print(f'Config: {MDIR}/config.pkl')
    print('=' * 50)
