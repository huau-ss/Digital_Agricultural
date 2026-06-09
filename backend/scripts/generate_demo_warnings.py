# -*- coding: utf-8 -*-
"""
演示用：生成测试预警消息
用于答辩展示，在没有真实预测数据时生成示例预警
"""
import os
import sys
import django

# 设置 Django 环境
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, base_dir)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'configs.settings')
django.setup()

from decimal import Decimal
from apps.users.models import CustomUser, SystemMessage
from apps.data_collection.models import AgriculturalProduct
from datetime import datetime


def create_demo_warnings():
    """创建演示用的预警消息"""

    print("=" * 50)
    print("生成演示预警消息")
    print("=" * 50)

    # 获取所有农产品
    products = AgriculturalProduct.objects.filter(is_active=True)
    if not products:
        print("错误：没有找到农产品数据")
        print("请先运行爬虫获取价格数据")
        return

    print(f"\n找到 {products.count()} 个农产品")

    # 获取一个测试用户
    user = CustomUser.objects.filter(is_active=True, is_approved=True).first()
    if not user:
        print("错误：没有找到可用的测试用户")
        return

    print(f"使用用户: {user.username} ({user.get_role_display()})")

    # 演示数据
    demo_warnings = [
        {
            'title': '【价格利好】白菜 价格看涨预警',
            'content': '''尊敬的农户用户，您好！

根据我们的 LSTM 价格预测模型分析，白菜 未来 14 天内价格预计将出现上涨。

📊 当前价格: 2.50 元/斤
📈 预测最高价: 3.20 元/斤
📊 预计涨幅: 28.0%
⏰ 预计在 7 天后达到峰值

💡 建议: 建议您适当延迟销售，以获得更好的价格收益。''',
            'priority': 'high',
            'direction': '上涨',
            'current_price': 2.50,
            'predicted_price': 3.20,
            'change_percent': 28.0,
            'change_days': 7,
        },
        {
            'title': '【价格预警】西红柿 价格下跌预警',
            'content': '''尊敬的农户用户，您好！

根据我们的 LSTM 价格预测模型分析，西红柿 未来 14 天内价格预计将出现下跌。

📊 当前价格: 4.80 元/斤
📉 预测最低价: 4.00 元/斤
📊 预计跌幅: 16.7%
⏰ 预计在 5 天后达到最低

💡 建议: 建议您密切关注市场行情，及时调整销售策略，尽快出售库存。''',
            'priority': 'urgent',
            'direction': '下跌',
            'current_price': 4.80,
            'predicted_price': 4.00,
            'change_percent': 16.7,
            'change_days': 5,
        },
        {
            'title': '【采购时机】黄瓜 价格下降预警',
            'content': '''尊敬的采购商用户，您好！

根据我们的 LSTM 价格预测模型分析，黄瓜 未来 14 天内价格预计将出现下降。

📊 当前价格: 3.20 元/斤
📉 预测最低价: 2.60 元/斤
📊 预计跌幅: 18.8%
⏰ 预计在 10 天后达到最低

💡 建议: 建议您适当推迟采购，等待价格下降后再进货，以降低成本。''',
            'priority': 'high',
            'direction': '下跌',
            'current_price': 3.20,
            'predicted_price': 2.60,
            'change_percent': 18.8,
            'change_days': 10,
        },
        {
            'title': '【采购提醒】土豆 价格上升预警',
            'content': '''尊敬的采购商用户，您好！

根据我们的 LSTM 价格预测模型分析，土豆 未来 14 天内价格预计将出现上涨。

📊 当前价格: 1.80 元/斤
📈 预测最高价: 2.25 元/斤
📊 预计涨幅: 25.0%
⏰ 预计在 8 天后达到峰值

💡 建议: 建议您尽快完成采购，避免价格上涨带来的成本增加。''',
            'priority': 'medium',
            'direction': '上涨',
            'current_price': 1.80,
            'predicted_price': 2.25,
            'change_percent': 25.0,
            'change_days': 8,
        },
        {
            'title': '【价格波动】胡萝卜 价格异常预警',
            'content': '''尊敬的农户用户，您好！

根据我们的 LSTM 价格预测模型分析，胡萝卜 未来 14 天内价格预计将出现较动。

📊 当前价格: 3.50 元/斤
📈 预测价格: 4.20 元/斤
📊 预计涨幅: 20.0%
⏰ 预计在 6 天后达到峰值

💡 建议: 建议您根据市场行情灵活调整销售策略。''',
            'priority': 'medium',
            'direction': '上涨',
            'current_price': 3.50,
            'predicted_price': 4.20,
            'change_percent': 20.0,
            'change_days': 6,
        },
    ]

    # 获取第一个产品作为关联
    product = products.first()

    # 清除该用户的旧预警消息（可选）
    deleted_count = SystemMessage.objects.filter(
        user=user,
        message_type='price_warning'
    ).delete()[0]

    if deleted_count > 0:
        print(f"已删除 {deleted_count} 条旧预警消息")

    # 创建新的预警消息
    created_count = 0
    for warning in demo_warnings:
        msg = SystemMessage.objects.create(
            user=user,
            title=warning['title'],
            content=warning['content'],
            message_type='price_warning',
            priority=warning['priority'],
            related_product_id=product.id,
            related_product_name=product.name,
            price_change_percent=Decimal(str(warning['change_percent'])),
            current_price=Decimal(str(warning['current_price'])),
            predicted_price=Decimal(str(warning['predicted_price'])),
            change_direction=warning['direction'],
            change_days=warning['change_days'],
            is_read=False  # 设为未读，展示红点效果
        )
        created_count += 1
        print(f"  [OK] 创建: {warning['title']}")

    print(f"\n成功创建 {created_count} 条演示预警消息")
    print("\n现在可以登录前端查看价格预警页面")
    print(f"登录账号: {user.username}")
    print("访问路径: 价格预警")


def clear_demo_warnings():
    """清除所有演示预警消息"""
    count = SystemMessage.objects.filter(message_type='price_warning').delete()[0]
    print(f"已清除 {count} 条预警消息")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='价格预警演示工具')
    parser.add_argument('--clear', action='store_true', help='清除所有预警消息')
    args = parser.parse_args()

    if args.clear:
        clear_demo_warnings()
    else:
        create_demo_warnings()
