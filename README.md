# 智慧农业大数据分析平台

基于 Django + Vue 3 + PyTorch 的农产品价格预测与大数据分析平台。

## 功能特性

- **数据采集**：爬取全国农产品批发市场价格数据，存入 MySQL 数据库
- **数据清洗**：异常值检测与剔除，数据质量保障
- **价格预测**：基于 LSTM 神经网络的农产品价格趋势预测
- **价格预警**：智能监测异常价格波动，及时预警
- **收益模拟**：农业种植收益测算与决策支持
- **数据可视化**：ECharts 交互图表，实时仪表盘

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Vue 3 + Vite + Element Plus + ECharts |
| 后端 | Django 4.2 + Django REST Framework |
| 数据库 | MySQL 8.0 |
| 深度学习 | PyTorch 2.x (LSTM) |
| 数据分析 | pandas + numpy + scikit-learn |

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

模型训练需要单独运行脚本：

```bash
# 方式一：双击运行
backend\scripts\train.bat

# 方式二：命令行
cd backend
python scripts/run_train.py
```

## API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/data-analysis/prediction/` | GET | 获取价格预测 |
| `/api/data-analysis/prediction/products/` | GET | 可预测产品列表 |
| `/api/data-analysis/warning/check/` | POST | 价格异常检测 |
| `/api/data-analysis/dashboard/summary/` | GET | 仪表盘摘要 |
| `/api/data-collection/prices/` | GET | 历史价格查询 |

## LSTM 模型说明

- **网络结构**：2 层 LSTM（hidden=64）+ Linear 输出层
- **滑动窗口**：7 天历史数据预测下一天
- **训练参数**：batch=16，lr=0.001，epochs=100
- **模型文件**：`backend/models/lstm/lstm_model.pth`
- **归一化器**：`backend/models/lstm/scaler.pkl`

## 数据库表

| 表名 | 说明 |
|------|------|
| `cleaned_price_data` | 清洗后的价格数据 |
| `agricultural_product` | 农产品基本信息 |
| `warning_rules` | 预警规则配置 |

## License

MIT License
