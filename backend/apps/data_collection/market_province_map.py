# -*- coding: utf-8 -*-
"""
市场名称到省份的映射工具
用于从市场名称中提取省份信息
"""

# 市场名称 → 省份 映射表
MARKET_TO_PROVINCE = {
    # 华北地区
    '北京新发地市场': '北京',
    '北京大洋路市场': '北京',
    '北京八里桥市场': '北京',
    '北京顺义市场': '北京',
    '天津金钟市场': '天津',
    '天津红旗市场': '天津',
    '天津韩家墅市场': '天津',
    '石家庄桥西市场': '河北',
    '石家庄西仰陵市场': '河北',
    '保定新发地市场': '河北',
    '唐山荷花坑市场': '河北',
    '邯郸金凤市场': '河北',
    '太原丈子头市场': '山西',
    '太原河西市场': '山西',
    '大同振华市场': '山西',
    '呼和浩特东瓦窑市场': '内蒙古',
    '包头市友谊市场': '内蒙古',
    '鄂尔多斯万家惠市场': '内蒙古',

    # 东北地区
    '沈阳八家子市场': '辽宁',
    '沈阳大东区市场': '辽宁',
    '大连双兴市场': '辽宁',
    '鞍山宁远市场': '辽宁',
    '长春蔬菜市场': '吉林',
    '长春东北亚市场': '吉林',
    '吉林东北亚市场': '吉林',
    '哈尔滨哈达市场': '黑龙江',
    '哈尔滨润恒市场': '黑龙江',
    '齐齐哈尔市场': '黑龙江',

    # 华东地区
    '上海江桥市场': '上海',
    '上海江杨市场': '上海',
    '上海农产品中心': '上海',
    '南京众彩市场': '江苏',
    '南京白云亭市场': '江苏',
    '苏州南环桥市场': '江苏',
    '无锡朝阳市场': '江苏',
    '常州凌家塘市场': '江苏',
    '扬州联谊市场': '江苏',
    '南通农副产品市场': '江苏',
    '徐州七里沟市场': '江苏',
    '杭州良渚市场': '浙江',
    '杭州农产品市场': '浙江',
    '宁波蔬菜市场': '浙江',
    '温州菜篮子市场': '浙江',
    '嘉兴蔬菜市场': '浙江',
    '金华农产品市场': '浙江',
    '合肥周谷堆市场': '安徽',
    '蚌埠海吉星市场': '安徽',
    '芜湖大地市场': '安徽',
    '福州海峡市场': '福建',
    '厦门闽南市场': '福建',
    '泉州禾富市场': '福建',
    '南昌农产品市场': '江西',
    '九江琵琶湖市场': '江西',
    '赣州华东城市场': '江西',
    '济南堤口市场': '山东',
    '青岛抚顺路市场': '山东',
    '青岛黄河路市场': '山东',
    '烟台幸福批发市场': '山东',
    '潍坊寿光市场': '山东',
    '临沂皇山市场': '山东',

    # 华中地区
    '武汉白沙洲市场': '湖北',
    '武汉皇经堂市场': '湖北',
    '宜昌三峡物流园': '湖北',
    '襄阳竹叶山市场': '湖北',
    '长沙红星市场': '湖南',
    '长沙马王堆市场': '湖南',
    '衡阳西园市场': '湖南',
    '株洲神农城市场': '湖南',
    '郑州万邦市场': '河南',
    '郑州陈砦市场': '河南',
    '开封宏进市场': '河南',

    # 华南地区
    '广州江南市场': '广东',
    '广州黄沙市场': '广东',
    '深圳海吉星市场': '广东',
    '深圳布吉市场': '广东',
    '佛山中南市场': '广东',
    '东莞信立市场': '广东',
    '珠海和平市场': '广东',
    '南宁海吉星市场': '广西',
    '柳州柳邕市场': '广西',
    '桂林五里店市场': '广西',
    '海口凤翔市场': '海南',
    '三亚鸿港市场': '海南',

    # 西南地区
    '成都雨润市场': '四川',
    '成都农产品中心': '四川',
    '成都聚合市场': '四川',
    '绵阳高水市场': '四川',
    '泸州楷模市场': '四川',
    '重庆双福市场': '重庆',
    '重庆观音桥市场': '重庆',
    '重庆新大兴市场': '重庆',
    '贵阳地利市场': '贵州',
    '贵阳五里冲市场': '贵州',
    '遵义播州市场': '贵州',
    '昆明王旗营市场': '云南',
    '昆明关上市场': '云南',
    '玉溪彩虹市场': '云南',
    '拉萨东嘎市场': '西藏',

    # 西北地区
    '西安新土门市场': '陕西',
    '西安朱雀市场': '陕西',
    '西安摩尔市场': '陕西',
    '咸阳新阳光市场': '陕西',
    '宝鸡人民路市场': '陕西',
    '兰州毅和市场': '甘肃',
    '兰州大青山市场': '甘肃',
    '天水麦积市场': '甘肃',
    '西宁青藏市场': '青海',
    '银川北环市场': '宁夏',
    '银川四季鲜市场': '宁夏',
    '乌鲁木齐北园春市场': '新疆',
    '乌鲁木齐九鼎市场': '新疆',
    '库尔勒万山红市场': '新疆',
}


def get_province_from_market(market_name: str) -> str:
    """
    从市场名称提取省份

    Args:
        market_name: 市场名称

    Returns:
        省份名称，如果未找到则返回空字符串
    """
    if not market_name:
        return ''

    # 精确匹配
    if market_name in MARKET_TO_PROVINCE:
        return MARKET_TO_PROVINCE[market_name]

    # 模糊匹配 - 检查是否包含已知的市场名称前缀
    for known_market, province in MARKET_TO_PROVINCE.items():
        if known_market in market_name or market_name in known_market:
            return province

    # 从市场名称中提取城市/省份名
    # 例如："北京新发地市场" -> "北京"
    if len(market_name) >= 2:
        # 检查前两个字是否是省份/直辖市
        prefix = market_name[:2]
        known_prefixes = ['北京', '上海', '天津', '重庆', '河北', '山西', '内蒙古',
                         '辽宁', '吉林', '黑龙江', '江苏', '浙江', '安徽', '福建',
                         '江西', '山东', '河南', '湖北', '湖南', '广东', '广西',
                         '海南', '四川', '贵州', '云南', '西藏', '陕西', '甘肃',
                         '青海', '宁夏', '新疆']
        for p in known_prefixes:
            if prefix == p:
                return p

    return ''


def get_all_provinces() -> list:
    """获取所有已知的省份列表"""
    provinces = set(MARKET_TO_PROVINCE.values())
    provinces.update(['北京', '上海', '天津', '重庆'])  # 确保直辖市在里面
    return sorted(list(provinces))


def get_markets_by_province(province: str) -> list:
    """获取指定省份的所有市场"""
    markets = [m for m, p in MARKET_TO_PROVINCE.items() if p == province]
    return sorted(markets)


def update_province_for_existing_records():
    """
    更新现有数据库记录的省份字段
    需要在Django shell中运行
    """
    from apps.data_collection.models import PriceHistory, CleanedPriceData

    updated_count = 0

    # 更新 PriceHistory
    for record in PriceHistory.objects.filter(province='').exclude(market_name=''):
        province = get_province_from_market(record.market_name)
        if province:
            record.province = province
            record.save(update_fields=['province'])
            updated_count += 1

    # 更新 CleanedPriceData
    for record in CleanedPriceData.objects.filter(province='').exclude(market_name=''):
        province = get_province_from_market(record.market_name)
        if province:
            record.province = province
            record.save(update_fields=['province'])
            updated_count += 1

    return updated_count
