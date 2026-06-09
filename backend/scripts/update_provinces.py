# -*- coding: utf-8 -*-
"""
更新现有数据的省份字段
根据市场名称自动提取省份信息
"""
import django
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'configs.settings')
django.setup()

from apps.data_collection.models import PriceHistory, CleanedPriceData
from apps.data_collection.market_province_map import get_province_from_market


def update_price_history_provinces():
    """更新 PriceHistory 表的省份字段"""
    print("=" * 60)
    print("更新 PriceHistory 表的省份字段...")
    print("=" * 60)

    # 找出省份为空的记录
    empty_records = PriceHistory.objects.filter(province='')
    total = empty_records.count()
    print(f"需要更新的记录数: {total}")

    updated = 0
    skipped = 0

    for record in empty_records:
        if not record.market_name:
            skipped += 1
            continue

        province = get_province_from_market(record.market_name)
        if province:
            record.province = province
            record.save(update_fields=['province'])
            updated += 1
        else:
            skipped += 1

        if updated % 100 == 0:
            print(f"已更新: {updated} 条")

    print(f"\nPriceHistory 更新完成:")
    print(f"  成功更新: {updated} 条")
    print(f"  跳过: {skipped} 条 (无市场名称或无法识别省份)")

    return updated, skipped


def update_cleaned_price_data_provinces():
    """更新 CleanedPriceData 表的省份字段"""
    print("\n" + "=" * 60)
    print("更新 CleanedPriceData 表的省份字段...")
    print("=" * 60)

    # 找出省份为空的记录
    empty_records = CleanedPriceData.objects.filter(province='')
    total = empty_records.count()
    print(f"需要更新的记录数: {total}")

    updated = 0
    skipped = 0

    for record in empty_records:
        if not record.market_name:
            skipped += 1
            continue

        province = get_province_from_market(record.market_name)
        if province:
            record.province = province
            record.save(update_fields=['province'])
            updated += 1
        else:
            skipped += 1

        if updated % 100 == 0:
            print(f"已更新: {updated} 条")

    print(f"\nCleanedPriceData 更新完成:")
    print(f"  成功更新: {updated} 条")
    print(f"  跳过: {skipped} 条 (无市场名称或无法识别省份)")

    return updated, skipped


def show_statistics():
    """显示省份分布统计"""
    print("\n" + "=" * 60)
    print("省份分布统计 (PriceHistory)")
    print("=" * 60)

    from django.db.models import Count

    stats = PriceHistory.objects.values('province').annotate(
        count=Count('id')
    ).order_by('-count')

    total = 0
    for s in stats:
        province = s['province'] or '(空)'
        print(f"  {province}: {s['count']} 条")
        total += s['count']

    print(f"\n总计: {total} 条记录")

    # 统计有省份和无省份的比例
    with_province = PriceHistory.objects.exclude(province='').count()
    without_province = PriceHistory.objects.filter(province='').count()
    print(f"\n有省份: {with_province} ({100*with_province/total:.1f}%)")
    print(f"无省份: {without_province} ({100*without_province/total:.1f}%)")


def main():
    print("\n" + "=" * 60)
    print("农产品价格数据 - 省份字段更新工具")
    print("=" * 60)

    # 更新 PriceHistory
    update_price_history_provinces()

    # 更新 CleanedPriceData
    update_cleaned_price_data_provinces()

    # 显示统计
    show_statistics()

    print("\n" + "=" * 60)
    print("更新完成!")
    print("=" * 60)


if __name__ == '__main__':
    main()
