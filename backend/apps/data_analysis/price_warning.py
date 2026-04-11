# -*- coding: utf-8 -*-
"""
价格预警检测服务
当系统通过 LSTM 预测到某产品未来价格较今日跌幅超过 10% 或涨幅超过 15% 时，
为相关用户生成一条预警记录。
"""
import logging
from decimal import Decimal
from django.utils import timezone
from apps.users.models import SystemMessage, CustomUser
from apps.data_collection.models import CleanedPriceData, AgriculturalProduct
from apps.data_analysis.lstm_service import predict_product_price

logger = logging.getLogger(__name__)

# 价格波动阈值
PRICE_DROP_THRESHOLD = 10  # 跌幅超过 10%
PRICE_RISE_THRESHOLD = 15  # 涨幅超过 15%


def check_price_warning(product_id, product_name=None):
    """
    检测产品价格是否出现异常波动并生成预警

    Args:
        product_id: 农产品ID
        product_name: 农产品名称（可选）

    Returns:
        dict: 包含预警信息或None
    """
    try:
        # 获取产品名称
        if not product_name:
            try:
                product = AgriculturalProduct.objects.get(id=product_id)
                product_name = product.name
            except AgriculturalProduct.DoesNotExist:
                product_name = f"产品{product_id}"

        # 获取当前价格（今日或最近一天的平均价）
        today = timezone.now().date()
        current_price_data = CleanedPriceData.objects.filter(
            product_id=product_id,
            date__lte=today
        ).order_by('-date').first()

        if not current_price_data:
            logger.info(f"产品 {product_name} 没有历史价格数据，跳过预警检测")
            return None

        current_price = float(current_price_data.avg_price) / 2  # 转为斤的价格

        if current_price <= 0:
            logger.warning(f"产品 {product_name} 当前价格无效: {current_price}")
            return None

        # 获取价格预测（未来14天）
        prediction_result = predict_product_price(product_id, future_days=14)

        if not prediction_result or not prediction_result.get('success'):
            logger.warning(f"产品 {product_name} 预测失败: {prediction_result.get('error', '未知错误')}")
            return None

        predicted_prices = prediction_result.get('prediction', {}).get('prices', [])

        if not predicted_prices:
            logger.warning(f"产品 {product_name} 没有预测价格数据")
            return None

        # 找到预测最高价和最低价
        max_predicted_price = max(predicted_prices) / 2  # 转为斤的价格
        min_predicted_price = min(predicted_prices) / 2  # 转为斤的价格

        # 计算涨跌幅
        price_change_percent = ((max_predicted_price - current_price) / current_price) * 100
        price_drop_percent = ((current_price - min_predicted_price) / current_price) * 100

        warning_info = None

        # 检测涨幅超过 15%
        if price_change_percent >= PRICE_RISE_THRESHOLD:
            max_change_day = predicted_prices.index(max(predicted_prices)) + 1
            warning_info = {
                'type': 'price_rise',
                'change_percent': round(price_change_percent, 2),
                'direction': '上涨',
                'current_price': current_price,
                'predicted_price': max_predicted_price,
                'change_day': max_change_day,
                'change_type': '涨幅',
            }
            logger.info(f"产品 {product_name} 检测到涨价预警: {price_change_percent:.2f}%")

        # 检测跌幅超过 10%
        elif price_drop_percent >= PRICE_DROP_THRESHOLD:
            min_change_day = predicted_prices.index(min(predicted_prices)) + 1
            warning_info = {
                'type': 'price_drop',
                'change_percent': round(price_drop_percent, 2),
                'direction': '下跌',
                'current_price': current_price,
                'predicted_price': min_predicted_price,
                'change_day': min_change_day,
                'change_type': '跌幅',
            }
            logger.info(f"产品 {product_name} 检测到跌价预警: {price_drop_percent:.2f}%")

        return warning_info

    except Exception as e:
        logger.error(f"检测产品 {product_id} 价格预警时发生错误: {str(e)}")
        return None


def generate_warning_messages(product_id, product_name, warning_info):
    """
    为相关用户生成预警消息

    Args:
        product_id: 农产品ID
        product_name: 农产品名称
        warning_info: 预警信息字典

    Returns:
        int: 生成的消息数量
    """
    if not warning_info:
        return 0

    message_count = 0
    change_percent = warning_info['change_percent']
    direction = warning_info['direction']
    current_price = warning_info['current_price']
    predicted_price = warning_info['predicted_price']
    change_day = warning_info['change_day']
    change_type = warning_info['change_type']

    # 获取所有相关用户（农户和采购商）
    users = CustomUser.objects.filter(is_active=True)

    for user in users:
        # 检查是否已经发送过类似的预警（最近24小时内）
        recent_warning = SystemMessage.objects.filter(
            user=user,
            product_id=product_id,
            created_at__gte=timezone.now() - timezone.timedelta(hours=24)
        ).exists()

        if recent_warning:
            continue

        # 根据用户角色生成不同的消息内容
        if user.role == 'farmer':
            if direction == '上涨':
                title = f"【价格利好】{product_name} 价格看涨预警"
                content = (
                    f"尊敬的农户用户，您好！\n\n"
                    f"根据我们的 LSTM 价格预测模型分析，{product_name} 未来 14 天内价格预计将出现上涨。\n\n"
                    f"📊 当前价格: {current_price:.2f} 元/斤\n"
                    f"📈 预测最高价: {predicted_price:.2f} 元/斤\n"
                    f"📊 预计{change_type}: {change_percent:.1f}%\n"
                    f"⏰ 预计在 {change_day} 天后达到峰值\n\n"
                    f"💡 建议: 建议您适当延迟销售，以获得更好的价格收益。"
                )
                priority = 'high'
            else:
                title = f"【价格预警】{product_name} 价格下跌预警"
                content = (
                    f"尊敬的农户用户，您好！\n\n"
                    f"根据我们的 LSTM 价格预测模型分析，{product_name} 未来 14 天内价格预计将出现下跌。\n\n"
                    f"📊 当前价格: {current_price:.2f} 元/斤\n"
                    f"📉 预测最低价: {predicted_price:.2f} 元/斤\n"
                    f"📊 预计{change_type}: {change_percent:.1f}%\n"
                    f"⏰ 预计在 {change_day} 天后达到最低\n\n"
                    f"💡 建议: 建议您密切关注市场行情，及时调整销售策略。"
                )
                priority = 'urgent'

        elif user.role == 'buyer':
            if direction == '下跌':
                title = f"【采购时机】{product_name} 价格下降预警"
                content = (
                    f"尊敬的采购商用户，您好！\n\n"
                    f"根据我们的 LSTM 价格预测模型分析，{product_name} 未来 14 天内价格预计将出现下降。\n\n"
                    f"📊 当前价格: {current_price:.2f} 元/斤\n"
                    f"📉 预测最低价: {predicted_price:.2f} 元/斤\n"
                    f"📊 预计{change_type}: {change_percent:.1f}%\n"
                    f"⏰ 预计在 {change_day} 天后达到最低\n\n"
                    f"💡 建议: 建议您适当推迟采购，等待价格下降后再进货，以降低成本。"
                )
                priority = 'high'
            else:
                title = f"【采购提醒】{product_name} 价格上升预警"
                content = (
                    f"尊敬的采购商用户，您好！\n\n"
                    f"根据我们的 LSTM 价格预测模型分析，{product_name} 未来 14 天内价格预计将出现上涨。\n\n"
                    f"📊 当前价格: {current_price:.2f} 元/斤\n"
                    f"📈 预测最高价: {predicted_price:.2f} 元/斤\n"
                    f"📊 预计{change_type}: {change_percent:.1f}%\n"
                    f"⏰ 预计在 {change_day} 天后达到峰值\n\n"
                    f"💡 建议: 建议您尽快完成采购，避免价格上涨带来的成本增加。"
                )
                priority = 'medium'
        else:
            # 管理员
            title = f"【系统通知】{product_name} 价格波动通知"
            content = (
                f"{product_name} 价格预计将{direction} {change_percent:.1f}%。\n\n"
                f"📊 当前价格: {current_price:.2f} 元/斤\n"
                f"📈 预测价格: {predicted_price:.2f} 元/斤\n"
                f"📊 {change_type}: {change_percent:.1f}%\n"
                f"⏰ 预计在 {change_day} 天后达到预测价格"
            )
            priority = 'medium'

        # 创建消息
        SystemMessage.objects.create(
            user=user,
            title=title,
            content=content,
            message_type='price_warning',
            priority=priority,
            related_product_id=product_id,
            related_product_name=product_name,
            price_change_percent=Decimal(str(change_percent))
        )
        message_count += 1

    return message_count


def run_price_warning_check():
    """
    执行所有农产品的价格预警检测
    这是模拟任务，实际可以配置为定时任务（如 celery beat）
    """
    logger.info("开始执行价格预警检测...")

    # 获取所有活跃的农产品
    products = AgriculturalProduct.objects.filter(is_active=True)

    total_warnings = 0
    for product in products:
        warning_info = check_price_warning(product.id, product.name)
        if warning_info:
            count = generate_warning_messages(product.id, product.name, warning_info)
            total_warnings += count

    logger.info(f"价格预警检测完成，共生成 {total_warnings} 条预警消息")
    return total_warnings


def check_single_product_warning(product_id):
    """
    检测单个产品的价格预警并生成消息

    Args:
        product_id: 农产品ID

    Returns:
        dict: 检测结果
    """
    try:
        product = AgriculturalProduct.objects.get(id=product_id)
        product_name = product.name
    except AgriculturalProduct.DoesNotExist:
        return {'success': False, 'error': '产品不存在'}

    warning_info = check_price_warning(product_id, product_name)

    if warning_info:
        count = generate_warning_messages(product_id, product_name, warning_info)
        return {
            'success': True,
            'has_warning': True,
            'warning_info': warning_info,
            'messages_sent': count
        }
    else:
        return {
            'success': True,
            'has_warning': False,
            'warning_info': None,
            'messages_sent': 0
        }
