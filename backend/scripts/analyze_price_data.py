"""
农产品价格数据分析脚本
对数据库中的历史价格数据进行分析和清洗
"""

import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List

import pandas as pd
import numpy as np

import django
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'configs.settings')
django.setup()

from apps.data_collection.models import AgriculturalProduct, PriceHistory

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PriceDataAnalyzer:
    """价格数据分析器"""

    def __init__(self):
        self.stats = {
            'total_analyzed': 0,
            'outliers_detected': 0,
            'records_updated': 0,
            'errors': 0
        }

    def load_data(self, product_id: int = None, days_back: int = 30) -> pd.DataFrame:
        """加载历史价格数据"""
        queryset = PriceHistory.objects.all()

        if product_id:
            queryset = queryset.filter(product_id=product_id)

        if days_back:
            start_date = datetime.now().date() - timedelta(days=days_back)
            queryset = queryset.filter(date__gte=start_date)

        data = list(queryset.values(
            'id', 'product_id', 'product__name', 'market_name',
            'date', 'avg_price', 'max_price', 'min_price'
        ))

        df = pd.DataFrame(data)
        logger.info(f"加载了 {len(df)} 条价格记录")
        return df

    def detect_outliers_zscore(self, df: pd.DataFrame, threshold: float = 3.0) -> pd.DataFrame:
        """使用 3σ 原则检测异常值"""
        df_result = df.copy()
        df_result['zscore_outlier'] = False

        for (product_id, market_name), group in df_result.groupby(['product_id', 'market_name']):
            if len(group) < 4:
                continue

            prices = group['avg_price'].astype(float)
            mean = prices.mean()
            std = prices.std()

            if std == 0:
                continue

            z_scores = np.abs((prices - mean) / std)
            mask = z_scores > threshold

            df_result.loc[mask.values, 'zscore_outlier'] = True
            outlier_count = mask.sum()
            if outlier_count > 0:
                self.stats['outliers_detected'] += outlier_count
                logger.debug(f"产品 {product_id} 市场 {market_name}: 检测到 {outlier_count} 个异常值")

        return df_result

    def detect_outliers_iqr(self, df: pd.DataFrame) -> pd.DataFrame:
        """使用 IQR 方法检测异常值"""
        df_result = df.copy()
        df_result['iqr_outlier'] = False

        for (product_id, market_name), group in df_result.groupby(['product_id', 'market_name']):
            if len(group) < 4:
                continue

            prices = group['avg_price'].astype(float)
            Q1 = prices.quantile(0.25)
            Q3 = prices.quantile(0.75)
            IQR = Q3 - Q1

            lower = Q1 - 1.5 * IQR
            upper = Q3 + 1.5 * IQR

            mask = (prices < lower) | (prices > upper)
            outlier_count = mask.sum()

            if outlier_count > 0:
                df_result.loc[mask.values, 'iqr_outlier'] = True
                self.stats['outliers_detected'] += outlier_count

        return df_result

    def analyze_product(self, product_id: int = None) -> Dict:
        """分析产品价格"""
        if product_id:
            queryset = PriceHistory.objects.filter(product_id=product_id)
            product = AgriculturalProduct.objects.get(id=product_id)
            product_name = product.name
        else:
            queryset = PriceHistory.objects.all()
            product_name = "全部产品"

        df = self.load_data(product_id=product_id)

        if df.empty:
            return {'error': '没有数据'}

        stats = {
            'product_id': product_id,
            'product_name': product_name,
            'total_records': len(df),
            'market_count': df['market_name'].nunique(),
            'date_range': {
                'start': str(df['date'].min()),
                'end': str(df['date'].max())
            }
        }

        # 价格统计
        stats['price_stats'] = {
            'avg': float(df['avg_price'].mean()),
            'min': float(df['avg_price'].min()),
            'max': float(df['avg_price'].max()),
            'std': float(df['avg_price'].std()),
            'median': float(df['avg_price'].median())
        }

        # 市场统计
        market_stats = df.groupby('market_name').agg({
            'avg_price': ['mean', 'std', 'count']
        }).round(4)
        market_stats.columns = ['avg_price', 'price_std', 'record_count']
        stats['market_stats'] = market_stats.to_dict('index')

        return stats

    def remove_duplicates(self) -> int:
        """删除重复记录"""
        duplicates = PriceHistory.objects.values('product_id', 'market_name', 'date').annotate(
            count=models.Count('id')
        ).filter(count__gt=1)

        removed = 0
        for dup in duplicates:
            records = PriceHistory.objects.filter(
                product_id=dup['product_id'],
                market_name=dup['market_name'],
                date=dup['date']
            ).order_by('created_at')

            # 保留第一条，删除其余
            for record in list(records)[1:]:
                record.delete()
                removed += 1

        logger.info(f"删除 {removed} 条重复记录")
        return removed

    def generate_report(self, product_id: int = None) -> Dict:
        """生成分析报告"""
        logger.info("=" * 60)
        logger.info("开始生成价格数据分析报告")
        logger.info("=" * 60)

        report = {}

        if product_id:
            try:
                product = AgriculturalProduct.objects.get(id=product_id)
                report['product'] = {
                    'id': product.id,
                    'name': product.name,
                    'category': product.category,
                    'origin': product.origin
                }
            except AgriculturalProduct.DoesNotExist:
                return {'error': '产品不存在'}

        # 加载数据
        df = self.load_data(product_id=product_id, days_back=90)

        if df.empty:
            return {'error': '没有可分析的数据'}

        # 检测异常值
        df = self.detect_outliers_zscore(df)
        df = self.detect_outliers_iqr(df)
        df['is_outlier'] = df['zscore_outlier'] | df['iqr_outlier']

        # 更新异常值标记
        outlier_ids = df[df['is_outlier']]['id'].tolist()
        if outlier_ids:
            PriceHistory.objects.filter(id__in=outlier_ids).update(remarks='异常值')
            self.stats['records_updated'] = len(outlier_ids)

        report['summary'] = {
            'total_records': len(df),
            'outliers_detected': int(df['is_outlier'].sum()),
            'clean_records': len(df) - int(df['is_outlier'].sum())
        }

        report['price_statistics'] = {
            'overall': {
                'mean': round(float(df['avg_price'].mean()), 4),
                'median': round(float(df['avg_price'].median()), 4),
                'std': round(float(df['avg_price'].std()), 4),
                'min': round(float(df['avg_price'].min()), 4),
                'max': round(float(df['avg_price'].max()), 4)
            }
        }

        # 按市场统计
        market_summary = df.groupby('market_name').agg({
            'avg_price': ['mean', 'count']
        })
        market_summary.columns = ['avg_price', 'count']
        market_summary = market_summary.sort_values('avg_price', ascending=False)
        report['market_ranking'] = market_summary.head(10).to_dict('index')

        self.print_stats()
        return report

    def print_stats(self):
        """打印统计信息"""
        logger.info("=" * 50)
        logger.info("分析完成，统计如下：")
        logger.info(f"  分析记录数: {self.stats['total_analyzed']}")
        logger.info(f"  异常值数量: {self.stats['outliers_detected']}")
        logger.info(f"  更新记录数: {self.stats['records_updated']}")
        logger.info(f"  错误数量: {self.stats['errors']}")
        logger.info("=" * 50)


def main():
    """主函数"""
    analyzer = PriceDataAnalyzer()

    # 分析所有产品
    report = analyzer.generate_report()

    if 'error' in report:
        logger.error(report['error'])
        return

    logger.info("\n分析报告:")
    logger.info(f"总记录数: {report['summary']['total_records']}")
    logger.info(f"异常值: {report['summary']['outliers_detected']}")
    logger.info(f"清洁记录: {report['summary']['clean_records']}")

    logger.info("\n价格统计:")
    for key, value in report['price_statistics']['overall'].items():
        logger.info(f"  {key}: {value}")


if __name__ == '__main__':
    from django.db import models
    main()
