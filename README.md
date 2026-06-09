# 智慧农业大数据分析平台

基于 Django + Vue 3 + PyTorch 的农产品价格预测与大数据分析平台。

## 功能特性

- **数据采集**：爬取全国农产品批发市场价格数据，存入 MySQL 数据库
- **数据清洗**：异常值检测与剔除，数据质量保障
- **价格预测**：基于 LSTM 神经网络的农产品价格趋势预测（支持 57+ 农产品专用模型）
- **价格预警**：智能监测异常价格波动，及时预警
- **收益模拟**：农业种植收益测算与决策支持
- **数据可视化**：ECharts 交互图表，实时仪表盘
- **测试模块**：功能测试 + 性能测试

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Vue 3 + Vite + Element Plus + ECharts |
| 后端 | Django 4.2 + Django REST Framework |
| 数据库 | MySQL 8.0 |
| 深度学习 | PyTorch 2.x (LSTM) |
| 数据分析 | pandas + numpy + scikit-learn |
| 测试 | unittest + Django TestCase |

## 项目结构

```
Digital Agriculture/
├── backend/                    # Django 后端
│   ├── apps/
│   │   ├── data_collection/   # 数据采集模块
│   │   ├── data_analysis/     # 数据分析模块（LSTM 预测）
│   │   ├── decision_support/  # 决策支持模块
│   │   └── users/            # 用户认证模块
│   ├── configs/               # Django 配置
│   ├── scripts/               # 运维脚本（爬虫、训练）
│   ├── models/                # LSTM 模型文件
│   │   ├── lstm/             # 通用 LSTM 模型
│   │   └── lstm_per_product/  # 产品专用 LSTM 模型（57个）
│   ├── tests/                 # 测试模块
│   │   ├── test_functional.py    # 功能测试
│   │   └── test_performance.py    # 性能测试
│   ├── requirements.txt
│   └── manage.py
│
├── frontend/                   # Vue 3 前端
│   ├── src/
│   │   ├── api/              # API 接口
│   │   ├── components/       # 通用组件
│   │   ├── views/            # 页面视图
│   │   └── router/           # 路由配置
│   ├── package.json
│   └── vite.config.js
│
└── README.md
```

## 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/huau-ss/Digital_Agricultural.git
cd Digital_Agricultural
```

### 2. 后端安装

```bash
cd backend

# 创建虚拟环境（推荐）
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置数据库连接 (backend/configs/settings.py)

# 数据库迁移
python manage.py migrate

# 启动服务器
python manage.py runserver
```

### 3. 前端安装

```bash
cd frontend

# 安装依赖
npm install

# 开发模式
npm run dev

# 生产构建
npm run build
```

### 4. LSTM 模型训练

```bash
# 方式一：双击运行
backend\scripts\train.bat

# 方式二：命令行
cd backend
python scripts/run_train.py

# 方式三：训练产品专用模型
cd backend
python scripts/train_lstm_per_product.py
```

### 5. 运行测试

```bash
cd backend

# 运行功能测试（22个测试项）
python tests/test_functional.py

# 运行性能测试
python tests/test_performance.py
```

## API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/data-analysis/prediction/` | GET | 获取价格预测 |
| `/api/data-analysis/prediction/products/` | GET | 可预测产品列表 |
| `/api/data-analysis/warning/check/` | POST | 价格异常检测 |
| `/api/data-analysis/warning/products/` | GET | 预警产品列表 |
| `/api/data-analysis/dashboard/summary/` | GET | 仪表盘摘要 |
| `/api/data-collection/products/` | GET | 产品列表 |
| `/api/data-collection/cleaned-prices/` | GET | 清洗后价格数据 |
| `/api/data-collection/price-history/` | GET | 历史价格查询 |

## LSTM 模型说明

### 模型架构

- **网络结构**：2 层 LSTM（hidden=64）+ Linear 输出层 + Dropout 0.2
- **滑动窗口**：7 天历史数据预测下一天
- **训练参数**：batch=16，lr=0.001，epochs=100
- **激活函数**：ReLU

### 模型类型

| 模型 | 路径 | 说明 |
|------|------|------|
| 通用模型 | `models/lstm/lstm_model.pth` | 所有产品共用一个模型 |
| 专用模型 | `models/lstm_per_product/lstm_p{id}.pth` | 每个产品独立模型（57个） |

### 预测准确性

- 平均 MAPE: ~4.5%
- 预测差异: 1% ~ 9%（与历史均价对比）

## 测试模块

### 功能测试 (`tests/test_functional.py`)

| 测试类别 | 测试项数 |
|---------|---------|
| 数据采集测试 | 7 |
| 价格预测测试 | 7 |
| 预警功能测试 | 4 |
| 可视化测试 | 4 |

### 性能测试 (`tests/test_performance.py`)

| 测试类别 | 测试项数 |
|---------|---------|
| API 性能测试 | 8 |
| 数据库性能测试 | 8 |
| 模型预测性能测试 | 4 |
| 负载测试 | 1 |

### 测试运行示例

```
============================================================
数字农业平台 - 功能测试
============================================================

数据采集功能测试:
[1] 测试产品列表API...  - 产品总数: 73
[2] 测试价格历史API...  - 获取记录数: 64411
...

价格预测功能测试:
[1] 测试价格预测API基础功能...  - 历史均价: 2.38
                                 - 预测均价: 2.52
                                 - 差异: 5.69%
...

============================================================
测试总结
============================================================
测试总数: 22
成功: 17
失败: 5
```

## 数据库表

| 表名 | 说明 |
|------|------|
| `agricultural_products` | 农产品基本信息（73种产品） |
| `cleaned_price_data` | 清洗后的价格数据（15万+条） |
| `price_history` | 原始价格历史数据 |
| `order` | 订单/交易记录 |
| `trade_info` | 供需信息 |
| `order_status_log` | 订单状态日志 |

## 数据规模

- **产品种类**: 73 种农产品
- **价格记录**: 15 万+ 条
- **覆盖省份**: 30+ 个省/直辖市
- **市场数量**: 36 个批发市场
- **数据周期**: 最近 120 天

## License

MIT License
