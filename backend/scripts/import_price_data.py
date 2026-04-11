"""
农产品价格数据导入脚本
从 CSV 文件导入价格数据到数据库
"""

import csv
import logging
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

import django
import os
import sys

# 设置 Django 环境
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'configs.settings')
django.setup()

from apps.data_collection.models import AgriculturalProduct, PriceHistory

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PriceDataImporter:
    """价格数据导入器"""

    def __init__(self):
        self.stats = {
            'total_rows': 0,
            'success_count': 0,
            'duplicate_count': 0,
            'error_count': 0,
            'new_products': 0
        }

    def parse_date(self, date_str):
        """解析日期字符串"""
        date_formats = ['%Y-%m-%d', '%Y/%m/%d', '%Y%m%d', '%d-%m-%Y', '%d/%m/%Y']
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str.strip(), fmt).date()
            except ValueError:
                continue
        return None

    def parse_decimal(self, value, default=None):
        """解析数字"""
        if not value or str(value).strip() == '':
            return default
        try:
            return Decimal(str(value).strip())
        except (InvalidOperation, ValueError):
            return default

    def get_or_create_product(self, product_name: str, category: str = 'other', origin: str = '') -> AgriculturalProduct:
        """获取或创建农产品"""
        product_name = product_name.strip()
        if not product_name:
            return None

        product, created = AgriculturalProduct.objects.get_or_create(
            name=product_name,
            defaults={
                'category': category,
                'origin': origin.strip(),
                'description': '从CSV导入',
            }
        )
        if created:
            self.stats['new_products'] += 1
            logger.info(f"新增产品: {product_name}")
        return product

    def import_from_csv(self, csv_path: str, product_name: str = None, category: str = 'other', origin: str = ''):
        """
        从 CSV 文件导入数据

        CSV 格式：
        date, market_name, avg_price, max_price, min_price, volume, source, remarks

        Args:
            csv_path: CSV 文件路径
            product_name: 产品名称（如果 CSV 中没有产品名列）
            category: 产品类别
            origin: 产地
        """
        csv_file = Path(csv_path)
        if not csv_file.exists():
            logger.error(f"文件不存在: {csv_path}")
            return

        logger.info(f"开始导入文件: {csv_path}")

        with open(csv_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)

            for row in reader:
                self.stats['total_rows'] += 1

                try:
                    # 获取产品名称
                    name = row.get('product_name') or row.get('name') or product_name
                    if not name:
                        logger.warning(f"第 {self.stats['total_rows']} 行缺少产品名称，跳过")
                        self.stats['error_count'] += 1
                        continue

                    # 创建/获取产品
                    product = self.get_or_create_product(name, category, origin)
                    if not product:
                        self.stats['error_count'] += 1
                        continue

                    # 解析日期
                    date_str = row.get('date', '')
                    record_date = self.parse_date(date_str)
                    if not record_date:
                        logger.warning(f"第 {self.stats['total_rows']} 行日期格式错误: {date_str}")
                        self.stats['error_count'] += 1
                        continue

                    # 解析价格
                    market = row.get('market_name', '未知市场').strip()
                    avg_price = self.parse_decimal(row.get('avg_price') or row.get('price') or row.get('average_price'))
                    max_price = self.parse_decimal(row.get('max_price') or row.get('high_price'))
                    min_price = self.parse_decimal(row.get('min_price') or row.get('low_price'))
                    volume = self.parse_decimal(row.get('volume', 0), 0)
                    source = row.get('source', 'CSV导入')
                    remarks = row.get('remarks', '')

                    if not avg_price:
                        logger.warning(f"第 {self.stats['total_rows']} 行缺少平均价格")
                        self.stats['error_count'] += 1
                        continue

                    # 检查是否重复
                    exists = PriceHistory.objects.filter(
                        product=product,
                        market_name=market,
                        date=record_date
                    ).exists()

                    if exists:
                        self.stats['duplicate_count'] += 1
                        continue

                    # 创建记录
                    PriceHistory.objects.create(
                        product=product,
                        date=record_date,
                        market_name=market,
                        avg_price=avg_price,
                        max_price=max_price,
                        min_price=min_price,
                        volume=int(volume) if volume else None,
                        source=source,
                        remarks=remarks
                    )

                    self.stats['success_count'] += 1

                except Exception as e:
                    logger.error(f"第 {self.stats['total_rows']} 行处理失败: {e}")
                    self.stats['error_count'] += 1

        self.print_stats()

    def print_stats(self):
        """打印统计信息"""
        logger.info("=" * 50)
        logger.info("导入完成，统计如下：")
        logger.info(f"  总行数: {self.stats['total_rows']}")
        logger.info(f"  成功导入: {self.stats['success_count']}")
        logger.info(f"  新增产品: {self.stats['new_products']}")
        logger.info(f"  重复跳过: {self.stats['duplicate_count']}")
        logger.info(f"  错误数量: {self.stats['error_count']}")
        logger.info("=" * 50)


def main():
    """主函数"""
    importer = PriceDataImporter()

    # 示例：从 data/sample_prices.csv 导入
    # 实际使用时修改为你的 CSV 文件路径
    csv_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'sample_prices.csv')

    if os.path.exists(csv_path):
        importer.import_from_csv(csv_path, product_name='示例产品', category='grain')
    else:
        logger.info(f"示例文件不存在: {csv_path}")
        logger.info("请使用以下命令导入数据:")
        logger.info("  python scripts/import_price_data.py <csv文件路径> [产品名称] [类别] [产地]")


if __name__ == '__main__':
    main()
