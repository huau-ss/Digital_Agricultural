# -*- coding: utf-8 -*-
"""
LSTM 价格预测服务
基于 PyTorch 的 LSTM 模型进行农产品价格预测
"""
import os
import sys
import django

# Django 环境配置（必须在 import django 之前设置）
# lstm_service.py 在 backend/apps/data_analysis/ 下
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# BASE_DIR = 'Digital Agriculture'，settings.py 在 backend/configs/ 下
SETTINGS_DIR = os.path.join(BASE_DIR, 'backend', 'configs')
if SETTINGS_DIR not in sys.path:
    sys.path.insert(0, SETTINGS_DIR)

# backend 目录本身也要加入（因为 Django 应用在 backend/apps/ 下）
BACKEND_DIR = os.path.join(BASE_DIR, 'backend')
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'configs.settings')
django.setup()

import numpy as np
import torch
import torch.nn as nn
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from datetime import datetime, timedelta
import joblib
from django.conf import settings

# 模型保存路径
# 优先使用产品专用模型目录
MODEL_DIR = os.path.join(settings.BASE_DIR, 'models', 'lstm_per_product')
GENERAL_MODEL_DIR = os.path.join(settings.BASE_DIR, 'models', 'lstm')


class LSTMModel(nn.Module):
    """LSTM 价格预测模型（与训练脚本保持一致）"""

    def __init__(self, input_size=1, hidden_size=64, num_layers=2, output_size=1, dropout=0.2):
        super(LSTMModel, self).__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers

        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0
        )
        self.fc = nn.Linear(hidden_size, output_size)

    def forward(self, x):
        lstm_out, _ = self.lstm(x)
        return self.fc(lstm_out[:, -1, :])


class LSTMPredictor:
    """LSTM 预测器封装类"""

    SEQ_LENGTH = 7
    HIDDEN_SIZE = 64
    NUM_LAYERS = 2
    DROPOUT = 0.2

    def __init__(self, product_id=None):
        self.product_id = product_id
        self.model = None
        self.scaler = None
        self.device = torch.device('cpu')

    def get_model_path(self):
        """获取模型路径，优先使用产品专用模型"""
        if self.product_id:
            # 优先：产品专用模型
            product_model_path = os.path.join(MODEL_DIR, f'lstm_p{self.product_id}.pth')
            if os.path.exists(product_model_path):
                return product_model_path
            # 其次：通用模型
            general_path = os.path.join(GENERAL_MODEL_DIR, 'lstm_model.pth')
            if os.path.exists(general_path):
                return general_path
        return os.path.join(GENERAL_MODEL_DIR, 'lstm_model.pth')

    def get_scaler_path(self):
        """获取归一化器路径，优先使用产品专用 scaler"""
        if self.product_id:
            # 优先：产品专用 scaler
            product_scaler_path = os.path.join(MODEL_DIR, f'scaler_p{self.product_id}.pkl')
            if os.path.exists(product_scaler_path):
                return product_scaler_path
            # 其次：通用 scaler
            general_path = os.path.join(GENERAL_MODEL_DIR, 'scaler.pkl')
            if os.path.exists(general_path):
                return general_path
        return os.path.join(GENERAL_MODEL_DIR, 'scaler.pkl')

    def load_model_and_scaler(self):
        """加载预训练模型和归一化器"""
        model_path = self.get_model_path()

        if not os.path.exists(model_path):
            model_path = os.path.join(MODEL_DIR, 'lstm_general.pth')
            if not os.path.exists(model_path):
                model_path = os.path.join(MODEL_DIR, 'lstm_model.pth')
                if not os.path.exists(model_path):
                    return False, False

        scaler_path = self.get_scaler_path()
        if not os.path.exists(scaler_path):
            scaler_path = os.path.join(MODEL_DIR, 'scaler.pkl')

        # 加载模型
        self.model = LSTMModel(
            input_size=1,
            hidden_size=self.HIDDEN_SIZE,
            num_layers=self.NUM_LAYERS,
            output_size=1,
            dropout=self.DROPOUT
        ).to(self.device)
        self.model.load_state_dict(torch.load(model_path, map_location=self.device))
        self.model.eval()

        # 加载归一化器
        if os.path.exists(scaler_path):
            self.scaler = joblib.load(scaler_path)
        else:
            self.scaler = MinMaxScaler(feature_range=(0, 1))

        return True, True

    def predict_future(self, historical_prices, future_days=7):
        """预测未来价格（自回归预测）"""
        if len(historical_prices) < 5:
            raise ValueError(f"历史数据不足，需要至少 5 天数据，当前只有 {len(historical_prices)} 天")

        loaded = self.load_model_and_scaler()
        if not loaded[0]:
            raise FileNotFoundError("未找到预训练模型，请先运行训练脚本！")

        # 计算当前数据的 min/max 用于归一化（根据数据本身而非全局 scaler）
        prices_array = np.array(historical_prices).reshape(-1, 1)
        data_min = prices_array.min()
        data_max = prices_array.max()

        # 如果数据范围太小（可能全是相同值），使用默认范围
        if data_max - data_min < 0.1:
            data_min = data_min - 0.5
            data_max = data_max + 0.5

        # 使用模型训练时的 scaler 进行归一化（基于全局数据范围）
        # 这样可以保证与训练时的一致性
        scaled_history = self.scaler.transform(prices_array)

        last_date = datetime.now().date()
        dates = []
        is_prediction = []

        for i in range(len(historical_prices)):
            d = last_date - timedelta(days=len(historical_prices) - 1 - i)
            dates.append(d.isoformat())
            is_prediction.append(False)

        # 只用最后 SEQ_LENGTH 天数据
        current_seq = scaled_history[-self.SEQ_LENGTH:].reshape(1, -1, 1)
        current_seq = torch.FloatTensor(current_seq).to(self.device)

        predictions = []
        for _ in range(future_days):
            with torch.no_grad():
                pred = self.model(current_seq)
                pred_value = pred.cpu().numpy()[0, 0]
                predictions.append(pred_value)

                current_seq = current_seq.cpu().numpy()
                current_seq = np.roll(current_seq, -1, axis=1)
                current_seq[0, -1, 0] = pred_value
                current_seq = torch.FloatTensor(current_seq).to(self.device)

        predictions = np.array(predictions).reshape(-1, 1)
        predictions_original = self.scaler.inverse_transform(predictions).flatten()

        # 添加约束：预测值不应偏离历史数据太远
        history_mean = np.mean(historical_prices)
        history_std = np.std(historical_prices) if np.std(historical_prices) > 0 else 0.5

        constrained_predictions = []
        for p in predictions_original:
            # 限制预测值在历史均值 ± 2 倍标准差范围内（更严格的约束）
            lower = history_mean - 2 * history_std
            upper = history_mean + 2 * history_std
            if lower < 0:
                lower = 0
            constrained_p = max(lower, min(upper, p))
            constrained_predictions.append(constrained_p)

        predictions_original = [round(float(p), 2) for p in constrained_predictions]

        for i in range(future_days):
            future_date = last_date + timedelta(days=i + 1)
            dates.append(future_date.isoformat())
            is_prediction.append(True)

        all_prices = list(historical_prices) + predictions_original
        return dates, all_prices, is_prediction

    def predict_single_step(self, recent_prices):
        """单步预测：基于最近数据预测下一天价格"""
        if len(recent_prices) < self.SEQ_LENGTH:
            raise ValueError(f"需要至少 {self.SEQ_LENGTH} 天数据")

        loaded = self.load_model_and_scaler()
        if not loaded[0]:
            raise FileNotFoundError("未找到预训练模型！")

        prices_array = np.array(recent_prices).reshape(-1, 1)
        scaled = self.scaler.transform(prices_array)
        X = torch.FloatTensor(scaled.reshape(1, -1, 1)).to(self.device)

        with torch.no_grad():
            pred = self.model(X)
            pred_value = self.scaler.inverse_transform(pred.cpu().numpy().reshape(-1, 1))[0, 0]

        return round(float(pred_value), 2)


def get_product_price_history(product_id, days=60):
    """获取产品的历史价格数据"""
    from apps.data_collection.models import CleanedPriceData

    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days)

    price_data = CleanedPriceData.objects.filter(
        product_id=product_id,
        date__gte=start_date,
        date__lte=end_date
    ).values('date', 'avg_price').order_by('date')

    daily_prices = {}
    for item in price_data:
        date_str = item['date'].strftime('%Y-%m-%d')
        if date_str not in daily_prices:
            daily_prices[date_str] = []
        daily_prices[date_str].append(float(item['avg_price']))

    prices = []
    for date_str in sorted(daily_prices.keys()):
        avg_price = sum(daily_prices[date_str]) / len(daily_prices[date_str])
        prices.append(round(avg_price, 2))

    return prices


def predict_product_price(product_id, future_days=7):
    """预测产品未来价格的主函数"""
    # 尝试获取最多60天历史数据
    historical_prices = get_product_price_history(product_id, days=60)

    # 降低最低要求，从12天改为7天（SEQ_LENGTH=7）
    min_required = 10  # 至少需要10天数据才能预测

    if len(historical_prices) < min_required:
        return {
            'success': False,
            'error': f'历史数据不足，需要至少 {min_required} 天，当前只有 {len(historical_prices)} 天',
            'product_id': product_id,
            'historical': {'dates': [], 'prices': []},
            'prediction': {'dates': [], 'prices': []}
        }

    try:
        predictor = LSTMPredictor(product_id)
        dates, prices, is_prediction = predictor.predict_future(historical_prices, future_days)

        historical_dates = [d for d, p, is_p in zip(dates, prices, is_prediction) if not is_p]
        historical_prices_list = [round(p, 2) for p, is_p in zip(prices, is_prediction) if not is_p]
        future_dates = [d for d, p, is_p in zip(dates, prices, is_prediction) if is_p]
        future_prices = [round(p, 2) for p, is_p in zip(prices, is_prediction) if is_p]

        return {
            'success': True,
            'product_id': product_id,
            'historical': {
                'dates': historical_dates,
                'prices': historical_prices_list
            },
            'prediction': {
                'dates': future_dates,
                'prices': future_prices
            },
            'metrics': {
                'seq_length': LSTMPredictor.SEQ_LENGTH,
                'model_version': 'v1.0',
                'updated_at': datetime.now().isoformat()
            }
        }

    except FileNotFoundError as e:
        return {
            'success': False,
            'error': '模型文件不存在，请先训练模型',
            'product_id': product_id,
            'historical': {'dates': [], 'prices': []},
            'prediction': {'dates': [], 'prices': []}
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'product_id': product_id,
            'historical': {'dates': [], 'prices': []},
            'prediction': {'dates': [], 'prices': []}
        }
