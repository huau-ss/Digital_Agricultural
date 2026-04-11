# -*- coding: utf-8 -*-
"""
农产品价格数据清洗脚本
对历史价格数据进行清洗和异常值检测，并写入 cleaned_price_data 表
"""

import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional

import pandas as pd
import numpy as np
from django.db import models

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
            'total_processed': 0,
            'duplicates_removed': 0,
            'outliers_marked': 0,
            'cleaned_inserted': 0,
            'cleaned_updated': 0,
            'errors': 0
        }

    def load_data(self, days_back: int = None, product_id: int = None) -> pd.DataFrame:
        """加载价格数据"""
        queryset = PriceHistory.objects.filter(remarks__isnull=True).exclude(remarks='异常值')

        if product_id:
            queryset = queryset.filter(product_id=product_id)

        if days_back:
            start_date = datetime.now().date() - timedelta(days=days_back)
            queryset = queryset.filter(date__gte=start_date)

        data = list(queryset.values(
            'id', 'product_id', 'product__name', 'market_name',
            'date', 'avg_price', 'max_price', 'min_price', 'volume', 'source'
        ))

        df = pd.DataFrame(data)
        logger.info(f"加载了 {len(df)} 条原始记录")
        return df

    def remove_duplicates(self) -> int:
        """删除重复记录"""
        duplicates = (
            PriceHistory.objects
            .values('product_id', 'market_name', 'date')
            .annotate(count=models.Count('id'))
            .filter(count__gt=1)
        )

        removed = 0
        for dup in duplicates:
            records = (
                PriceHistory.objects
                .filter(
                    product_id=dup['product_id'],
                    market_name=dup['market_name'],
                    date=dup['date']
                )
                .order_by('created_at')
            )

            for record in list(records)[1:]:
                record.delete()
                removed += 1

        self.stats['duplicates_removed'] += removed
        logger.info(f"删除 {removed} 条重复记录")
        return removed

    def detect_outliers_zscore(self, df: pd.DataFrame, threshold: float = 3.0) -> pd.DataFrame:
        """
        使用 3σ 原则检测异常值
        """
        df_result = df.copy()
        df_result['is_outlier_zscore'] = False

        for (product_id, market_name), group in df_result.groupby(['product_id', 'market_name']):
            if len(group) < 4:
                continue

            prices = pd.to_numeric(group['avg_price'], errors='coerce')
            mean = prices.mean()
            std = prices.std()

            if pd.isna(std) or std == 0:
                continue

            z_scores = np.abs((prices - mean) / std)
            mask = z_scores > threshold

            if mask.any():
                df_result.loc[mask.values, 'is_outlier_zscore'] = True
                self.stats['outliers_marked'] += mask.sum()

        return df_result

    def detect_outliers_iqr(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        使用 IQR（四分位距）方法检测异常值
        """
        df_result = df.copy()
        df_result['is_outlier_iqr'] = False

        for (product_id, market_name), group in df_result.groupby(['product_id', 'market_name']):
            if len(group) < 4:
                continue

            prices = pd.to_numeric(group['avg_price'], errors='coerce').dropna()

            if len(prices) < 4:
                continue

            Q1 = prices.quantile(0.25)
            Q3 = prices.quantile(0.75)
            IQR = Q3 - Q1

            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR

            mask = (prices < lower_bound) | (prices > upper_bound)

            if mask.any():
                outlier_indices = prices[mask].index
                df_result.loc[outlier_indices, 'is_outlier_iqr'] = True
                self.stats['outliers_marked'] += mask.sum()

        return df_result

    def merge_outlier_flags(self, df: pd.DataFrame) -> pd.DataFrame:
        """合并异常值检测结果"""
        df_result = df.copy()

        if 'is_outlier_iqr' in df_result.columns and 'is_outlier_zscore' in df_result.columns:
            df_result['is_outlier'] = df_result['is_outlier_iqr'] | df_result['is_outlier_zscore']
        elif 'is_outlier_iqr' in df_result.columns:
            df_result['is_outlier'] = df_result['is_outlier_iqr']
        elif 'is_outlier_zscore' in df_result.columns:
            df_result['is_outlier'] = df_result['is_outlier_zscore']
        else:
            df_result['is_outlier'] = False

        return df_result

    def write_cleaned_data(self, df: pd.DataFrame) -> Dict[str, int]:
        """
        将清洗后的数据写入 cleaned_price_data 表
        """
        inserted = 0
        updated = 0
        errors = 0

        for _, row in df.iterrows():
            try:
                product_id = row['product_id']
                market_name = row['market_name']
                date = row['date']
                avg_price = Decimal(str(row['avg_price']))
                is_outlier = row.get('is_outlier', False)

                max_price = Decimal(str(row['max_price'])) if pd.notna(row.get('max_price')) else None
                min_price = Decimal(str(row['min_price'])) if pd.notna(row.get('min_price')) else None
                volume = int(row['volume']) if pd.notna(row.get('volume')) else None
                source = row.get('source', '')

                outlier_reason = 'IQR异常' if row.get('is_outlier_iqr', False) else (
                    'Z-score异常' if row.get('is_outlier_zscore', False) else '')

                # 查找是否已存在
                existing = CleanedPriceData.objects.filter(
                    product_id=product_id,
                    market_name=market_name,
                    date=date
                ).first()

                if existing:
                    # 更新现有记录
                    existing.avg_price = avg_price
                    existing.max_price = max_price
                    existing.min_price = min_price
                    existing.volume = volume
                    existing.source = source
                    existing.is_outlier = is_outlier
                    existing.outlier_reason = outlier_reason if is_outlier else ''
                    existing.save()
                    updated += 1
                else:
                    # 创建新记录
                    CleanedPriceData.objects.create(
                        product_id=product_id,
                        market_name=market_name,
                        date=date,
                        avg_price=avg_price,
                        max_price=max_price,
                        min_price=min_price,
                        volume=volume,
                        source=source,
                        is_outlier=is_outlier,
                        outlier_reason=outlier_reason if is_outlier else ''
                    )
                    inserted += 1

            except Exception as e:
                errors += 1
                logger.debug(f"写入清洗数据失败: {e}")
                continue

        self.stats['cleaned_inserted'] += inserted
        self.stats['cleaned_updated'] += updated
        self.stats['errors'] += errors

        logger.info(f"清洗数据写入完成: 新增 {inserted} 条, 更新 {updated} 条, 错误 {errors} 条")

        return {'inserted': inserted, 'updated': updated, 'errors': errors}

    def clean(
        self,
        days_back: int = 30,
        product_id: int = None,
        method: str = 'both',
        remove_duplicates_flag: bool = True
    ) -> Dict:
        """
        执行数据清洗流程

        Args:
            days_back: 处理最近 N 天的数据
            product_id: 指定产品ID（None 表示所有产品）
            method: 异常值检测方法 ('iqr', 'zscore', 'both')
            remove_duplicates_flag: 是否删除重复记录
        """
        logger.info("=" * 60)
        logger.info("开始数据清洗流程")
        logger.info(f"处理范围: 最近 {days_back} 天")
        logger.info(f"检测方法: {method}")
        logger.info("=" * 60)

        # 1. 删除重复记录
        if remove_duplicates_flag:
            self.remove_duplicates()

        # 2. 加载数据
        df = self.load_data(days_back=days_back, product_id=product_id)

        if df.empty:
            logger.warning("没有需要处理的数据")
            return self.stats

        self.stats['total_processed'] = len(df)

        # 3. 异常值检测
        if method in ['iqr', 'both']:
            df = self.detect_outliers_iqr(df)
        if method in ['zscore', 'both']:
            df = self.detect_outliers_zscore(df)

        # 合并异常标记
        df = self.merge_outlier_flags(df)

        outlier_count = df['is_outlier'].sum()
        logger.info(f"异常值检测完成，共检测到 {outlier_count} 个异常值")

        # 4. 写入清洗后的数据
        self.write_cleaned_data(df)

        self.print_stats()
        return self.stats

    def get_statistics(self, product_id: int = None) -> Dict:
        """获取数据统计信息"""
        queryset = CleanedPriceData.objects.all()

        if product_id:
            queryset = queryset.filter(product_id=product_id)

        total = queryset.count()
        outlier_count = queryset.filter(is_outlier=True).count()

        from django.db.models import Avg, Max, Min, Sum

        stats = queryset.aggregate(
            avg_avg_price=Avg('avg_price'),
            max_avg_price=Max('avg_price'),
            min_avg_price=Min('avg_price'),
            total_volume=Sum('volume')
        )

        return {
            'total_records': total,
            'outlier_count': outlier_count,
            'clean_count': total - outlier_count,
            'avg_price': stats['avg_avg_price'],
            'max_price': stats['max_avg_price'],
            'min_price': stats['min_avg_price'],
            'total_volume': stats['total_volume']
        }

    def print_stats(self):
        """打印清洗统计"""
        logger.info("=" * 60)
        logger.info("数据清洗完成，统计如下：")
        logger.info(f"  处理记录数: {self.stats['total_processed']}")
        logger.info(f"  删除重复: {self.stats['duplicates_removed']}")
        logger.info(f"  标记异常值: {self.stats['outliers_marked']}")
        logger.info(f"  清洗数据新增: {self.stats['cleaned_inserted']}")
        logger.info(f"  清洗数据更新: {self.stats['cleaned_updated']}")
        logger.info(f"  错误数量: {self.stats['errors']}")
        logger.info("=" * 60)


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='农产品价格数据清洗脚本')
    parser.add_argument('--days', type=int, default=30, help='处理最近N天的数据（默认30天）')
    parser.add_argument('--product-id', type=int, default=None, help='指定产品ID')
    parser.add_argument('--method', type=str, default='both', choices=['iqr', 'zscore', 'both'],
                        help='异常值检测方法')
    parser.add_argument('--no-remove-dup', action='store_true', help='不删除重复记录')

    args = parser.parse_args()

    cleaner = PriceDataCleaner()

    # 执行清洗
    cleaner.clean(
        days_back=args.days,
        product_id=args.product_id,
        method=args.method,
        remove_duplicates_flag=not args.no_remove_dup
    )

    # 打印统计信息
    stats = cleaner.get_statistics(product_id=args.product_id)
    logger.info("\n清洗后数据统计:")
    logger.info(f"  总记录数: {stats['total_records']}")
    logger.info(f"  异常值: {stats['outlier_count']}")
    logger.info(f"  清洁记录: {stats['clean_count']}")


if __name__ == '__main__':
    main()
