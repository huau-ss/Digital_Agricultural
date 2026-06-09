# -*- coding: utf-8 -*-
"""
LSTM 价格预测服务
基于 PyTorch 的 LSTM 模型进行农产品价格预测
"""
import os
import sys
import django

# Django 环境配置（必须在 import django 之前设置）
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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

    def __init__(self, product_id=None, market_name=None):
        # 初始化参数
        self.product_id = product_id
        self.market_name = market_name  # 地区/市场名称
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
        self.model.load_state_dict(torch.load(model_path, map_location=self.device))    # 加载模型参数
        self.model.eval()    # 设置为评估模式

        # 加载归一化器
        if os.path.exists(scaler_path):
            self.scaler = joblib.load(scaler_path)
        else:
            self.scaler = MinMaxScaler(feature_range=(0, 1))

        return True, True

    def predict_future(self, historical_prices, future_days=7):
        """预测未来价格（自回归预测）"""
        if len(historical_prices) < 7:
            raise ValueError(f"历史数据不足，需要至少 5 天数据，当前只有 {len(historical_prices)} 天")

        loaded = self.load_model_and_scaler()    # 加载模型和归一化器
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

        #添加历史日期
        for i in range(len(historical_prices)):
            d = last_date - timedelta(days=len(historical_prices) - 1 - i)
            dates.append(d.isoformat())
            is_prediction.append(False)

        # 只用最后 SEQ_LENGTH 天数据
        current_seq = scaled_history[-self.SEQ_LENGTH:].reshape(1, -1, 1)
        current_seq = torch.FloatTensor(current_seq).to(self.device)

        # 自回归预测未来价格
        predictions = []
        for _ in range(future_days):
            with torch.no_grad():    # 不计算梯度       
                pred = self.model(current_seq)    # 预测
                pred_value = pred.cpu().numpy()[0, 0]    # 预测值
                predictions.append(pred_value)    # 添加到预测列表

                current_seq = current_seq.cpu().numpy()    # 更新当前序列
                current_seq = np.roll(current_seq, -1, axis=1)    # 左移一位
                current_seq[0, -1, 0] = pred_value    # 最后一位填入预测值
                current_seq = torch.FloatTensor(current_seq).to(self.device)    # 更新当前序列
        #反归一化
        predictions = np.array(predictions).reshape(-1, 1)    
        predictions_original = self.scaler.inverse_transform(predictions).flatten()    

        # 添加约束：预测值不应偏离历史数据太远
        history_mean = np.mean(historical_prices)    # 历史均值
        history_std = np.std(historical_prices) if np.std(historical_prices) > 0 else 0.5
        # 限制预测值在历史均值 ± 2 倍标准差范围内（更严格的约束）
        constrained_predictions = []
        for p in predictions_original:
            lower = history_mean - 2 * history_std
            upper = history_mean + 2 * history_std
            if lower < 0:
                lower = 0
            constrained_p = max(lower, min(upper, p))
            constrained_predictions.append(constrained_p)

        #四舍五入
        predictions_original = [round(float(p), 2) for p in constrained_predictions]    
        #添加预测日期
        for i in range(future_days):
            future_date = last_date + timedelta(days=i + 1)
            dates.append(future_date.isoformat())
            is_prediction.append(True)    # 添加预测标志

        all_prices = list(historical_prices) + predictions_original    # 添加预测价格
        return dates, all_prices, is_prediction    # 返回日期、价格和预测标志

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


def get_product_price_history(product_id, days=60, market_name=None, province=None):
    """获取产品的历史价格数据

    Args:
        product_id: 产品ID
        days: 获取天数，默认60天
        market_name: 市场名称（可选），与 province 二选一
        province: 省份名称（可选），会匹配该省份下所有市场的平均价格
    """
    from apps.data_collection.models import CleanedPriceData

    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days)

    filters = {
        'product_id': product_id,
        'date__gte': start_date,
        'date__lte': end_date,
        'is_outlier': False  # 只查询清洗后的正常数据
    }

    # 优先使用省份，如果指定了省份则忽略 market_name
    if province:
        filters['province'] = province
    elif market_name:
        filters['market_name'] = market_name

    price_data = CleanedPriceData.objects.filter(**filters).values('date', 'avg_price').order_by('date')


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


def get_available_markets(product_id):
    """获取指定产品可用的地区/市场列表"""
    from apps.data_collection.models import CleanedPriceData
    from datetime import datetime, timedelta

    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=90)

    markets = CleanedPriceData.objects.filter(
        product_id=product_id,
        date__gte=start_date,
        date__lte=end_date
    ).values_list('market_name', flat=True).distinct().order_by('market_name')

    return list(markets)


def get_available_provinces(product_id):
    """获取指定产品可用的省份列表"""
    from apps.data_collection.models import CleanedPriceData
    from datetime import datetime, timedelta

    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=90)

    provinces = CleanedPriceData.objects.filter(
        product_id=product_id,
        date__gte=start_date,
        date__lte=end_date
    ).exclude(province='').values_list('province', flat=True).distinct().order_by('province')

    return list(provinces)


def get_prediction_metrics(product_id, seq_length):
    """从 model_registry.pkl 读取该产品的真实评估指标"""
    registry_path = os.path.join(MODEL_DIR, 'model_registry.pkl')
    if not os.path.exists(registry_path):
        return {'seq_length': seq_length, 'model_version': 'unknown', 'updated_at': None}

    try:
        registry = joblib.load(registry_path)
        key = str(product_id) if str(product_id) in registry else product_id
        if key in registry:
            r = registry[key]
            return {
                'seq_length': seq_length,
                'model_version': 'v1.0',
                'updated_at': datetime.now().isoformat(),
                'rmse': round(r.get('rmse', 0), 4),
                'mae': round(r.get('mae', 0), 4),
                'r2': round(r.get('r2', 0), 4),
                'mape': round(r.get('mape', 0), 2),
                'data_points': r.get('data_points', 0),
            }
        return {'seq_length': seq_length, 'model_version': 'unknown', 'updated_at': None}
    except Exception:
        return {'seq_length': seq_length, 'model_version': 'unknown', 'updated_at': None}


def predict_product_price(product_id, future_days=7, market_name=None, province=None):
    """预测产品未来价格的主函数

    Args:
        product_id: 产品ID
        future_days: 预测天数，默认7天
        market_name: 市场名称（可选），与 province 二选一，province 优先
        province: 省份名称（可选），会使用该省份下所有市场的平均价格
    """
    # 尝试获取最多90天历史数据（90天覆盖更完整的数据周期）
    historical_prices = get_product_price_history(product_id, days=90, market_name=market_name, province=province)

    # 降低最低要求，从12天改为7天（SEQ_LENGTH=7）
    min_required = 10  # 至少需要10天数据才能预测

    if len(historical_prices) < min_required:
        return {
            'success': False,
            'error': f'历史数据不足，需要至少 {min_required} 天，当前只有 {len(historical_prices)} 天',
            'product_id': product_id,
            'market_name': market_name,
            'province': province,
            'historical': {'dates': [], 'prices': []},
            'prediction': {'dates': [], 'prices': []}
        }

    try:
        #创建预测器并预测
        predictor = LSTMPredictor(product_id, market_name=province or market_name)
        dates, prices, is_prediction = predictor.predict_future(historical_prices, future_days)

        #分离历史日期和预测日期
        historical_dates = [d for d, p, is_p in zip(dates, prices, is_prediction) if not is_p]
        historical_prices_list = [round(p, 2) for p, is_p in zip(prices, is_prediction) if not is_p]
        future_dates = [d for d, p, is_p in zip(dates, prices, is_prediction) if is_p]
        future_prices = [round(p, 2) for p, is_p in zip(prices, is_prediction) if is_p]

        #返回结果
        return {
            'success': True,
            'product_id': product_id,
            'province': province,
            'market_name': province or (market_name or '全国平均'),
            'historical': {
                'dates': historical_dates,
                'prices': historical_prices_list
            },
            'prediction': {
                'dates': future_dates,
                'prices': future_prices
            },
            'metrics': get_prediction_metrics(product_id, LSTMPredictor.SEQ_LENGTH),
        }

    except FileNotFoundError as e:
        return {
            'success': False,
            'error': '模型文件不存在，请先训练模型',
            'product_id': product_id,
            'province': province,
            'market_name': province or market_name,
            'historical': {'dates': [], 'prices': []},
            'prediction': {'dates': [], 'prices': []}
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'product_id': product_id,
            'province': province,
            'market_name': province or market_name,
            'historical': {'dates': [], 'prices': []},
            'prediction': {'dates': [], 'prices': []}
        }
