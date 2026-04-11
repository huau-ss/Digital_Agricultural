# -*- coding: utf-8 -*-
"""
LSTM 训练启动器
"""
import subprocess, sys, os

python_exe = r'E:\python3.11\python.exe'
python_dir = r'E:\python3.11'
output_dir = r'E:\PyCharm 2025.2.1.1\pythonProjects\Digital Agriculture\backend\models\lstm'

# 训练脚本 - 关键：先 import torch，再 import pandas！
script = r'''# -*- coding: utf-8 -*-
import os, sys

# 清理环境
for key in list(os.environ.keys()):
    if 'PYCHARM' in key.upper():
        del os.environ[key]
sys.path = [p for p in sys.path if 'PyCharm' not in p and p != '']
sys.path.insert(0, r'E:\python3.11\Lib\site-packages')
sys.path.insert(0, r'E:\python3.11')
os.chdir(r'E:\python3.11')

# 关键顺序：先 import torch，再 import pandas
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

DB = {'host':'localhost','port':3306,'user':'root','password':'123456','database':'digital_agriculture','charset':'utf8mb4'}
MDIR = r'E:\PyCharm 2025.2.1.1\pythonProjects\Digital Agriculture\backend\models\lstm'
os.makedirs(MDIR, exist_ok=True)
print('Output dir exists:', os.path.exists(MDIR))

SL, HS, NL, DR = 7, 64, 2, 0.2
LR, BS, EP = 0.001, 16, 100

class LSTM(nn.Module):
    def __init__(self):
        super().__init__()
        self.l = nn.LSTM(1, HS, NL, batch_first=True, dropout=DR if NL>1 else 0)
        self.f = nn.Linear(HS, 1)
    def forward(self, x):
        return self.f(self.l(x)[0][:,-1,:])

print('=' * 60)
print('LSTM Training - Agricultural Price Prediction')
print('=' * 60)

conn = pymysql.connect(**DB)
try:
    ed = datetime.now().date()
    sd = ed - timedelta(days=365)
    df = pd.read_sql('SELECT date, avg_price FROM cleaned_price_data WHERE date>=%s AND date<=%s AND is_outlier=0 ORDER BY date ASC', conn, params=(sd, ed))
finally:
    conn.close()
df = df.groupby('date')['avg_price'].mean().reset_index().sort_values('date').reset_index(drop=True)
print('Loaded {} records'.format(len(df)))

scaler = MinMaxScaler(feature_range=(0, 1))
scaled = scaler.fit_transform(df['avg_price'].values.reshape(-1, 1))
X, Y = [], []
for i in range(len(scaled)-SL):
    X.append(scaled[i:i+SL])
    Y.append(scaled[i+SL])
X, Y = np.array(X, dtype=np.float32), np.array(Y, dtype=np.float32)
print('X={}, Y={}'.format(X.shape, Y.shape))

ts = int(len(X)*0.8)
X_tr, Y_tr = torch.FloatTensor(X[:ts]), torch.FloatTensor(Y[:ts])
X_te, Y_te = torch.FloatTensor(X[ts:]), torch.FloatTensor(Y[ts:])
tr_ld = DataLoader(TensorDataset(X_tr, Y_tr), batch_size=BS, shuffle=True)
te_ld = DataLoader(TensorDataset(X_te, Y_te), batch_size=BS)
print('Train={}, Test={}'.format(len(X_tr), len(X_te)))

model = LSTM()
crit = nn.MSELoss()
opt = torch.optim.Adam(model.parameters(), lr=LR)
tr_l, te_l = [], []

print('=' * 60)
for ep in range(EP):
    model.train()
    el = 0
    for bx, by in tr_ld:
        p = model(bx)
        l = crit(p, by)
        opt.zero_grad()
        l.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step()
        el += l.item()
    tr_l.append(el/len(tr_ld))
    model.eval()
    etl = 0
    with torch.no_grad():
        for bx, by in te_ld:
            etl += crit(model(bx), by).item()
    te_l.append(etl/len(te_ld))
    if (ep+1) % 10 == 0:
        print('Epoch [{0:3d}/{1}] Train={2:.6f} Test={3:.6f}'.format(ep+1, EP, tr_l[-1], te_l[-1]))

model.eval()
preds = []
with torch.no_grad():
    for bx, _ in te_ld:
        preds.extend(model(bx).numpy().flatten())
preds = scaler.inverse_transform(np.array(preds).reshape(-1, 1))
y_te = scaler.inverse_transform(Y_te.numpy().reshape(-1, 1))
rmse = np.sqrt(mean_squared_error(y_te, preds))
mae = mean_absolute_error(y_te, preds)
r2 = r2_score(y_te, preds)
print('=' * 60)
print('RMSE={:.4f} MAE={:.4f} R2={:.4f}'.format(rmse, mae, r2))
print('=' * 60)

torch.save(model.state_dict(), os.path.join(MDIR, 'lstm_model.pth'))
joblib.dump(scaler, os.path.join(MDIR, 'scaler.pkl'))
print('Model saved!')
print('Scaler saved!')

plt.figure(figsize=(12, 6))
e = range(1, EP+1)
plt.plot(e, tr_l, 'b-', label='Train Loss', lw=2, marker='o', ms=2)
plt.plot(e, te_l, 'r-', label='Test Loss', lw=2, marker='s', ms=2)
plt.xlabel('Epoch')
plt.ylabel('Loss (MSE)')
plt.title('LSTM Training Loss Curve')
plt.legend(fontsize=11)
plt.grid(True, alpha=0.3)
plt.text(0.02, 0.98, 'Final: {:.6f}/{:.6f}'.format(tr_l[-1], te_l[-1]), transform=plt.gca().transAxes, fontsize=10, va='top')
plt.tight_layout()
plt.savefig(os.path.join(MDIR, 'training_loss_curve.png'), dpi=150)
plt.close()
print('Plot saved!')
print('Training Complete!')
'''

# 写入 E:\python3.11\_lstm_train.py
script_file = os.path.join(python_dir, '_lstm_train.py')
with open(script_file, 'w', encoding='utf-8') as f:
    f.write(script)

print("=" * 60)
print("LSTM Training Launcher")
print("=" * 60)
print("Writing script to:", script_file)

# 清理环境
new_env = os.environ.copy()
for key in list(new_env.keys()):
    if 'PYCHARM' in key.upper():
        del new_env[key]

# 运行
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
    try:
        print(line)
    except Exception:
        pass

# 清理
try:
    os.remove(script_file)
except:
    pass

print("=" * 60)
print("Exit code:", proc.returncode)
print("=" * 60)
