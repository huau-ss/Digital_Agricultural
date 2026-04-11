"""
农产品价格数据清洗脚本
从 price_history 表读取原始数据，清洗后存入 cleaned_price_data 表
"""

import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Tuple

import pandas as pd
import numpy as np

import django
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'configs.settings')
django.setup()

from apps.data_collection.models import AgriculturalProduct, PriceHistory, CleanedPriceData

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PriceDataCleaner:
    """价格数据清洗器"""

    def __init__(self):
        self.stats = {
            'total_source': 0,
            'total_cleaned': 0,
            'duplicates_skipped': 0,
            'outliers_zscore': 0,
            'outliers_iqr': 0,
            'errors': 0
        }

    def load_source_data(self) -> pd.DataFrame:
        """加载原始数据"""
        queryset = PriceHistory.objects.all().select_related('product').order_by('product_id', 'market_name', 'date')

        data = []
        for record in queryset:
            data.append({
                'id': record.id,
                'product_id': record.product_id,
                'product_name': record.product.name,
                'market_name': record.market_name,
                'date': record.date,
                'avg_price': float(record.avg_price),
                'max_price': float(record.max_price) if record.max_price else None,
                'min_price': float(record.min_price) if record.min_price else None,
                'volume': record.volume,
                'source': record.source,
            })

        df = pd.DataFrame(data)
        logger.info(f"加载了 {len(df)} 条原始数据")
        return df

    def detect_outliers_zscore(self, df: pd.DataFrame, threshold: float = 3.0) -> pd.DataFrame:
        """
        使用 3σ 原则（Z-score）检测异常值
        """
        df_result = df.copy()
        df_result['outlier_zscore'] = False
        df_result['reason_zscore'] = ''

        for (product_id, market_name), group in df_result.groupby(['product_id', 'market_name']):
            if len(group) < 5:
                continue

            prices = group['avg_price'].values
            mean = prices.mean()
            std = prices.std()

            if std == 0:
                continue

            z_scores = np.abs((prices - mean) / std)
            mask = z_scores > threshold

            if mask.any():
                outlier_count = mask.sum()
                self.stats['outliers_zscore'] += outlier_count
                df_result.loc[group.index[mask], 'outlier_zscore'] = True
                df_result.loc[group.index[mask], 'reason_zscore'] = f'Z-score>{threshold}'
                logger.debug(f"产品 {product_id} 市场 {market_name}: Z-score检测到 {outlier_count} 个异常值")

        return df_result

    def detect_outliers_iqr(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        使用 IQR（四分位距）方法检测异常值
        """
        df_result = df.copy()
        df_result['outlier_iqr'] = False
        df_result['reason_iqr'] = ''

        for (product_id, market_name), group in df_result.groupby(['product_id', 'market_name']):
            if len(group) < 5:
                continue

            prices = group['avg_price'].values

            Q1 = np.percentile(prices, 25)
            Q3 = np.percentile(prices, 75)
            IQR = Q3 - Q1

            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR

            mask = (prices < lower_bound) | (prices > upper_bound)

            if mask.any():
                outlier_count = mask.sum()
                self.stats['outliers_iqr'] += outlier_count
                df_result.loc[group.index[mask], 'outlier_iqr'] = True
                df_result.loc[group.index[mask], 'reason_iqr'] = 'IQR异常'
                logger.debug(f"产品 {product_id} 市场 {market_name}: IQR检测到 {outlier_count} 个异常值")

        return df_result

    def merge_outlier_flags(self, df: pd.DataFrame) -> pd.DataFrame:
        """合并异常值检测结果"""
        df_result = df.copy()

        # 任一方法检测到即为异常
        df_result['is_outlier'] = df_result['outlier_zscore'] | df_result['outlier_iqr']

        # 合并原因
        def combine_reason(row):
            reasons = []
            if row['outlier_zscore']:
                reasons.append(row['reason_zscore'])
            if row['outlier_iqr']:
                reasons.append(row['reason_iqr'])
            return '; '.join(filter(None, reasons))

        df_result['outlier_reason'] = df_result.apply(combine_reason, axis=1)

        # 删除临时列
        df_result = df_result.drop(columns=['outlier_zscore', 'reason_zscore', 'outlier_iqr', 'reason_iqr'])

        return df_result

    def save_to_cleaned_table(self, df: pd.DataFrame) -> int:
        """保存清洗后的数据到 cleaned_price_data 表"""
        saved_count = 0

        for _, row in df.iterrows():
            try:
                # 检查是否已存在
                exists = CleanedPriceData.objects.filter(
                    product_id=row['product_id'],
                    market_name=row['market_name'],
                    date=row['date']
                ).exists()

                if exists:
                    self.stats['duplicates_skipped'] += 1
                    continue

                # 创建清洗后的记录
                CleanedPriceData.objects.create(
                    product_id=row['product_id'],
                    date=row['date'],
                    market_name=row['market_name'],
                    avg_price=Decimal(str(round(row['avg_price'], 4))),
                    max_price=Decimal(str(round(row['max_price'], 4))) if pd.notna(row['max_price']) else None,
                    min_price=Decimal(str(round(row['min_price'], 4))) if pd.notna(row['min_price']) else None,
                    volume=row['volume'],
                    source=row['source'],
                    is_outlier=row['is_outlier'],
                    outlier_reason=row['outlier_reason']
                )

                saved_count += 1
                self.stats['total_cleaned'] += 1

            except Exception as e:
                logger.error(f"保存记录失败: {e}, product_id={row['product_id']}")
                self.stats['errors'] += 1

        return saved_count

    def run_cleaning(self) -> Dict:
        """
        执行完整的数据清洗流程
        """
        logger.info("=" * 60)
        logger.info("开始数据清洗流程")
        logger.info("=" * 60)

        # 1. 加载原始数据
        df = self.load_source_data()
        self.stats['total_source'] = len(df)

        if df.empty:
            logger.warning("没有原始数据")
            return self.stats

        # 2. Z-score 异常值检测（3σ原则）
        logger.info("执行 Z-score 异常值检测（3σ原则）...")
        df = self.detect_outliers_zscore(df, threshold=3.0)

        # 3. IQR 异常值检测
        logger.info("执行 IQR 异常值检测...")
        df = self.detect_outliers_iqr(df)

        # 4. 合并异常值结果
        df = self.merge_outlier_flags(df)

        outlier_count = df['is_outlier'].sum()
        logger.info(f"异常值检测完成，共检测到 {outlier_count} 个异常值")
        logger.info(f"  - Z-score 方法: {self.stats['outliers_zscore']} 个")
        logger.info(f"  - IQR 方法: {self.stats['outliers_iqr']} 个")

        # 5. 保存到清洗后的表
        logger.info("保存清洗后的数据到 cleaned_price_data 表...")
        saved = self.save_to_cleaned_table(df)
        logger.info(f"成功保存 {saved} 条清洗后的记录")

        self.print_stats()
        return self.stats

    def print_stats(self):
        """打印统计信息"""
        logger.info("=" * 60)
        logger.info("数据清洗完成，统计如下：")
        logger.info(f"  原始数据总数: {self.stats['total_source']}")
        logger.info(f"  清洗后保存: {self.stats['total_cleaned']}")
        logger.info(f"  重复跳过: {self.stats['duplicates_skipped']}")
        logger.info(f"  Z-score 异常值: {self.stats['outliers_zscore']}")
        logger.info(f"  IQR 异常值: {self.stats['outliers_iqr']}")
        logger.info(f"  错误数量: {self.stats['errors']}")
        logger.info("=" * 60)


def main():
    """主函数"""
    cleaner = PriceDataCleaner()
    cleaner.run_cleaning()


if __name__ == '__main__':
    main()
