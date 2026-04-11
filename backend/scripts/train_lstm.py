# -*- coding: utf-8 -*-
"""
农产品价格预测 LSTM 模型训练脚本
========================================
功能：
1. 从数据库读取清洗后的价格数据 (cleaned_price_data 表)
2. 使用 MinMaxScaler 归一化到 (0, 1)
3. create_sequences(data, seq_length) 滑动窗口构造特征 X 和标签 Y
4. 划分训练集 (80%) / 测试集 (20%)，封装为 DataLoader
5. PriceLSTM(nn.Module) 模型：2层 LSTM (hidden=64) + Linear 输出
6. MSELoss + Adam 优化器，100 epochs 训练
7. 保存：lstm_model.pth、scaler.pkl、training_loss_curve.png

使用方法:
    python scripts/train_lstm.py              # 默认参数
    python scripts/train_lstm.py --epochs 200  # 训练 200 轮
    python scripts/train_lstm.py --seq-length 10  # 滑动窗口 10 天
"""

# ================================================================
# 注意：本脚本需要在 PyCharm 之外运行（避免路径干扰 PyTorch DLL）
# 方式一：双击运行 train.bat
# 方式二：直接运行本脚本（如果您已解决 PyTorch DLL 问题）
# ================================================================

import subprocess
import sys
import os

python_exe = r'E:\python3.11\python.exe'
python_dir = r'E:\python3.11'
script_dir = os.path.dirname(os.path.abspath(__file__))
script_file = os.path.join(python_dir, '_lstm_train.py')

TRAIN_CODE = r'''# -*- coding: utf-8 -*-
import os, sys

# 解决 PyTorch DLL 加载问题
for key in list(os.environ.keys()):
    if 'PYCHARM' in key.upper():
        del os.environ[key]
sys.path = [p for p in sys.path if 'PyCharm' not in p and p != '']
sys.path.insert(0, r'E:\python3.11\Lib\site-packages')
sys.path.insert(0, r'E:\python3.11')
os.chdir(r'E:\python3.11')

# 导入库 - 关键：先 torch 再 pandas
import numpy as np
import matplotlib
matplotlib.use('Agg')
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
import pandas as pd
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

# 模型保存路径
MDIR = r'E:\PyCharm 2025.2.1.1\pythonProjects\Digital Agriculture\backend\models\lstm'
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


# ==================== 1. 数据准备 ====================

def load_data(days=365):
    """从数据库加载清洗后的价格数据"""
    conn = pymysql.connect(**DB)
    try:
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        df = pd.read_sql(
            "SELECT date, avg_price FROM cleaned_price_data "
            "WHERE date>=%s AND date<=%s AND is_outlier=0 ORDER BY date ASC",
            conn, params=(start_date, end_date)
        )
    finally:
        conn.close()
    # 按日期聚合（多市场取均值）
    df = df.groupby('date')['avg_price'].mean().reset_index()
    df = df.sort_values('date').reset_index(drop=True)
    return df


def create_sequences(data, seq_length):
    """
    使用滑动窗口构造特征 X 和标签 Y

    Args:
        data: 归一化后的价格数组，形状 (n_samples, 1)
        seq_length: 滑动窗口长度

    Returns:
        X: 特征数组，形状 (n_samples - seq_length, seq_length, 1)
        Y: 标签数组，形状 (n_samples - seq_length, 1)
    """
    X, Y = [], []
    for i in range(len(data) - seq_length):
        X.append(data[i:i + seq_length])
        Y.append(data[i + seq_length])
    return np.array(X, dtype=np.float32), np.array(Y, dtype=np.float32)


def prepare_dataloaders(X, Y, train_ratio=0.8, batch_size=32):
    """划分训练集/测试集并封装为 DataLoader"""
    train_size = int(len(X) * train_ratio)
    X_train, X_test = X[:train_size], X[train_size:]
    Y_train, Y_test = Y[:train_size], Y[train_size:]

    X_train = torch.FloatTensor(X_train)
    Y_train = torch.FloatTensor(Y_train)
    X_test = torch.FloatTensor(X_test)
    Y_test = torch.FloatTensor(Y_test)

    train_loader = DataLoader(
        TensorDataset(X_train, Y_train),
        batch_size=batch_size, shuffle=True
    )
    test_loader = DataLoader(
        TensorDataset(X_test, Y_test),
        batch_size=batch_size, shuffle=False
    )
    return train_loader, test_loader, Y_test


# ==================== 2. 模型定义 ====================

class PriceLSTM(nn.Module):
    """
    LSTM 价格预测模型
    结构: LSTM(input=1, hidden=64, layers=2, dropout=0.2) -> Linear(64 -> 1)
    """

    def __init__(self, input_size=1, hidden_size=64, num_layers=2, output_size=1, dropout=0.2):
        super(PriceLSTM, self).__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers

        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,  # (batch, seq, feature)
            dropout=dropout if num_layers > 1 else 0
        )
        self.fc = nn.Linear(hidden_size, output_size)

    def forward(self, x):
        lstm_out, _ = self.lstm(x)
        output = lstm_out[:, -1, :]  # 取最后一个时间步
        output = self.fc(output)
        return output


# ==================== 3. 训练过程 ====================

def train_model(model, train_loader, test_loader, Y_test, scaler, epochs=100, lr=0.001):
    """训练 LSTM 模型"""
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    train_losses, test_losses = [], []

    print("=" * 60)
    print("开始训练 LSTM 模型")
    print("=" * 60)

    for epoch in range(epochs):
        # 训练阶段
        model.train()
        epoch_loss = 0.0
        for batch_X, batch_Y in train_loader:
            pred = model(batch_X)
            loss = criterion(pred, batch_Y)
            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)  # 梯度裁剪
            optimizer.step()
            epoch_loss += loss.item()

        avg_train_loss = epoch_loss / len(train_loader)
        train_losses.append(avg_train_loss)

        # 验证阶段
        model.eval()
        epoch_test_loss = 0.0
        with torch.no_grad():
            for batch_X, batch_Y in test_loader:
                pred = model(batch_X)
                epoch_test_loss += criterion(pred, batch_Y).item()
        avg_test_loss = epoch_test_loss / len(test_loader)
        test_losses.append(avg_test_loss)

        # 每 10 轮打印一次 Loss
        if (epoch + 1) % 10 == 0 or epoch == 0:
            print("Epoch [{0:3d}/{1}] Train Loss: {2:.6f} | Test Loss: {3:.6f}".format(
                epoch + 1, epochs, avg_train_loss, avg_test_loss))

    return train_losses, test_losses


# ==================== 4. 模型保存 ====================

def save_model_and_scaler(model, scaler):
    """保存模型参数和归一化器"""
    torch.save(model.state_dict(), os.path.join(MDIR, 'lstm_model.pth'))
    print("模型已保存: lstm_model.pth")
    joblib.dump(scaler, os.path.join(MDIR, 'scaler.pkl'))
    print("归一化器已保存: scaler.pkl")


def plot_loss_curve(train_losses, test_losses):
    """绘制训练 Loss 下降曲线"""
    plt.figure(figsize=(12, 6))
    epochs = range(1, len(train_losses) + 1)
    plt.plot(epochs, train_losses, 'b-', label='Training Loss', linewidth=2, marker='o', markersize=2)
    plt.plot(epochs, test_losses, 'r-', label='Test Loss', linewidth=2, marker='s', markersize=2)
    plt.xlabel('Epoch', fontsize=12)
    plt.ylabel('Loss (MSE)', fontsize=12)
    plt.title('LSTM Model Training Loss Curve\n(Agricultural Product Price Prediction)', fontsize=14, fontweight='bold')
    plt.legend(fontsize=11)
    plt.grid(True, alpha=0.3)
    info_text = (
        "Final Training Loss: {0:.6f}\n"
        "Final Test Loss: {1:.6f}\n"
        "Total Epochs: {2}"
    ).format(train_losses[-1], test_losses[-1], len(train_losses))
    plt.text(0.02, 0.98, info_text, transform=plt.gca().transAxes,
             fontsize=10, verticalalignment='top',
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    plt.tight_layout()
    plt.savefig(os.path.join(MDIR, 'training_loss_curve.png'), dpi=150, bbox_inches='tight')
    plt.close()
    print("Loss 曲线图已保存: training_loss_curve.png")


def evaluate_model(model, test_loader, Y_test, scaler):
    """评估模型性能（反归一化后计算指标）"""
    model.eval()
    predictions = []
    with torch.no_grad():
        for batch_X, _ in test_loader:
            pred = model(batch_X)
            predictions.extend(pred.cpu().numpy().flatten())

    predictions = np.array(predictions).reshape(-1, 1)
    predictions_original = scaler.inverse_transform(predictions)
    Y_test_original = scaler.inverse_transform(Y_test.cpu().numpy().reshape(-1, 1))

    mse = mean_squared_error(Y_test_original, predictions_original)
    rmse = np.sqrt(mse)
    mae = mean_absolute_error(Y_test_original, predictions_original)
    r2 = r2_score(Y_test_original, predictions_original)
    mask = Y_test_original.flatten() != 0
    mape = (np.mean(np.abs((Y_test_original.flatten()[mask] - predictions_original.flatten()[mask])
                          / Y_test_original.flatten()[mask])) * 100) if mask.sum() > 0 else 0

    print("=" * 60)
    print("模型评估结果")
    print("=" * 60)
    print("  MSE:   {0:.4f}".format(mse))
    print("  RMSE:  {0:.4f}".format(rmse))
    print("  MAE:   {0:.4f}".format(mae))
    print("  R2:    {0:.4f}".format(r2))
    print("  MAPE:  {0:.4f}%".format(mape))


# ==================== 主函数 ====================

def main():
    import argparse
    parser = argparse.ArgumentParser(description='农产品价格预测 LSTM 模型训练')
    parser.add_argument('--epochs', type=int, default=EPOCHS, help='训练轮数 (默认100)')
    parser.add_argument('--seq-length', type=int, default=SEQ_LENGTH, help='滑动窗口长度 (默认7)')
    parser.add_argument('--batch-size', type=int, default=BATCH_SIZE, help='批次大小 (默认16)')
    parser.add_argument('--lr', type=float, default=LEARNING_RATE, help='学习率 (默认0.001)')
    parser.add_argument('--hidden-size', type=int, default=HIDDEN_SIZE, help='隐藏层维度 (默认64)')
    parser.add_argument('--num-layers', type=int, default=NUM_LAYERS, help='LSTM层数 (默认2)')
    parser.add_argument('--days', type=int, default=365, help='使用最近多少天的数据 (默认365)')
    args = parser.parse_args()

    print("=" * 60)
    print("农产品价格预测 LSTM 模型训练")
    print("=" * 60)
    print("滑动窗口: {0} | 隐藏层: {1} | 层数: {2}".format(
        args.seq_length, args.hidden_size, args.num_layers))
    print("训练轮数: {0} | 批次: {1} | 学习率: {2}".format(
        args.epochs, args.batch_size, args.lr))
    print("模型保存路径: {0}".format(MDIR))
    print("=" * 60)

    # 1. 加载数据
    print("正在加载数据...")
    df = load_data(days=args.days)
    print("加载了 {0} 条价格记录".format(len(df)))
    print("日期范围: {0} ~ {1}".format(df['date'].min(), df['date'].max()))

    if len(df) < args.seq_length + 10:
        print("错误: 数据量不足，至少需要 {0} 条记录".format(args.seq_length + 10))
        return

    # 2. 归一化
    scaler = MinMaxScaler(feature_range=(0, 1))
    prices = df['avg_price'].values.reshape(-1, 1)
    scaled_prices = scaler.fit_transform(prices)

    # 3. 构造序列
    X, Y = create_sequences(scaled_prices, args.seq_length)
    print("序列构造完成: X={0}, Y={1}".format(X.shape, Y.shape))

    # 4. 划分数据集
    train_loader, test_loader, Y_test = prepare_dataloaders(
        X, Y, train_ratio=TRAIN_RATIO, batch_size=args.batch_size
    )
    print("训练集: {0} 样本, 测试集: {1} 样本".format(
        len(train_loader.dataset.tensors[0]), len(test_loader.dataset.tensors[0])))

    # 5. 初始化模型
    model = PriceLSTM(
        input_size=1,
        hidden_size=args.hidden_size,
        num_layers=args.num_layers,
        output_size=1,
        dropout=DROPOUT
    )
    total_params = sum(p.numel() for p in model.parameters())
    print("\n模型结构:\n{0}".format(model))
    print("参数总量: {0:,}".format(total_params))

    # 6. 训练
    train_losses, test_losses = train_model(
        model, train_loader, test_loader, Y_test, scaler,
        epochs=args.epochs, lr=args.lr
    )

    # 7. 评估
    evaluate_model(model, test_loader, Y_test, scaler)

    # 8. 绘制 Loss 曲线
    plot_loss_curve(train_losses, test_losses)

    # 9. 保存
    save_model_and_scaler(model, scaler)

    print("=" * 60)
    print("训练完成！")
    print("  模型文件: {0}".format(os.path.join(MDIR, 'lstm_model.pth')))
    print("  归一化器: {0}".format(os.path.join(MDIR, 'scaler.pkl')))
    print("  Loss 曲线: {0}".format(os.path.join(MDIR, 'training_loss_curve.png')))
    print("=" * 60)


if __name__ == '__main__':
    main()
'''

# 写入临时训练脚本
with open(script_file, 'w', encoding='utf-8') as f:
    f.write(TRAIN_CODE)

print("=" * 60)
print("LSTM 训练启动器")
print("=" * 60)
print("正在写入训练脚本...")

# 清理环境
new_env = os.environ.copy()
for key in list(new_env.keys()):
    if 'PYCHARM' in key.upper():
        del new_env[key]

# 运行训练
proc = subprocess.Popen(
    [python_exe, script_file],
    cwd=python_dir,
    env=new_env,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
)
stdout, _ = proc.communicate()
out = stdout.decode('utf-8', errors='replace')
for line in out.split('\n'):
    print(line)

# 清理临时文件
try:
    os.remove(script_file)
except:
    pass

print("=" * 60)
print("退出码:", proc.returncode)
print("=" * 60)
