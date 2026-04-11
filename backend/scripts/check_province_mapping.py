# -*- coding: utf-8 -*-
import pymysql
import sys
sys.stdout.reconfigure(encoding='utf-8')

# 获取所有市场名称和对应的省份
conn = pymysql.connect(host='localhost', user='root', password='123456', database='digital_agriculture', charset='utf8mb4')
cursor = conn.cursor()

cursor.execute('SELECT DISTINCT market_name FROM cleaned_price_data')
markets = [row[0] for row in cursor.fetchall()]

# 省份映射逻辑
def get_province(market_name):
    if not market_name:
        return '其他'

    # 直接匹配
    market_province = {
        'Beijing Xinfadi': '北京',
        '北京新发地批发市场': '北京',
        '上海农产品中心批发市场': '上海',
        'Shanghai Agrip': '上海',
        '广州江南果菜批发市场': '广东',
        '深圳海吉星农产品物流园': '广东',
        '南京农副产品物流中心': '江苏',
        '南京众彩物流配送中心': '江苏',
        '杭州果品批发交易市场': '浙江',
        '武汉白沙洲农副产品大市场': '湖北',
        '成都农产品中心批发市场': '四川',
        '重庆双福国际农贸城': '重庆',
        '郑州万邦国际农产品物流城': '河南',
        '长沙红星农副产品大市场': '湖南',
        '西安欣桥农产品物流中心': '陕西',
        '哈尔滨润恒城农产品批发市场': '黑龙江',
        '沈阳八家子批发市场': '辽宁',
        '山东匡山农产品综合交易市场': '山东',
        '天津金钟农产品批发市场': '天津',
        '石家庄桥西蔬菜中心批发市场': '河北',
        '南昌深圳农产品中心批发市场': '江西',
        '福州海峡农产品批发市场': '福建',
        '厦门闽南农副产品物流中心': '福建',
        '昆明龙城农产品批发市场': '云南',
        '贵阳农产品物流园': '贵州',
        '兰州毅和农产品市场': '甘肃',
        '乌鲁木齐北园春农贸市场': '新疆',
        '合肥周谷堆农产品批发市场': '安徽',
        '太原市河西农产品有限公司': '山西',
        '呼和浩特馨昊佳农产品': '内蒙古',
        '南宁农产品交易中心': '广西',
        '海口南北水果市场': '海南',
    }

    if market_name in market_province:
        return market_province[market_name]

    # 模糊匹配
    if '北京' in market_name:
        return '北京'
    elif '上海' in market_name:
        return '上海'
    elif '广州' in market_name or '深圳' in market_name or '广东' in market_name:
        return '广东'
    elif '南京' in market_name or '江苏' in market_name:
        return '江苏'
    elif '杭州' in market_name or '浙江' in market_name:
        return '浙江'
    elif '武汉' in market_name or '湖北' in market_name:
        return '湖北'
    elif '成都' in market_name or '四川' in market_name:
        return '四川'
    elif '重庆' in market_name:
        return '重庆'
    elif '郑州' in market_name or '河南' in market_name:
        return '河南'
    elif '长沙' in market_name or '湖南' in market_name:
        return '湖南'
    elif '西安' in market_name or '陕西' in market_name:
        return '陕西'
    elif '哈尔滨' in market_name or '黑龙江' in market_name:
        return '黑龙江'
    elif '沈阳' in market_name or '辽宁' in market_name:
        return '辽宁'
    elif '山东' in market_name:
        return '山东'
    elif '天津' in market_name:
        return '天津'
    elif '石家庄' in market_name or '河北' in market_name:
        return '河北'
    elif '南昌' in market_name or '江西' in market_name:
        return '江西'
    elif '福州' in market_name or '厦门' in market_name or '福建' in market_name:
        return '福建'
    elif '昆明' in market_name or '云南' in market_name:
        return '云南'
    elif '贵阳' in market_name or '贵州' in market_name:
        return '贵州'
    elif '兰州' in market_name or '甘肃' in market_name:
        return '甘肃'
    elif '乌鲁木齐' in market_name or '新疆' in market_name:
        return '新疆'
    elif '合肥' in market_name or '安徽' in market_name:
        return '安徽'
    elif '太原' in market_name or '山西' in market_name:
        return '山西'
    elif '呼和浩特' in market_name or '内蒙古' in market_name:
        return '内蒙古'
    elif '南宁' in market_name or '广西' in market_name:
        return '广西'
    elif '海口' in market_name or '海南' in market_name:
        return '海南'

    return '其他'

print('市场名称 -> 省份映射:')
for market in markets:
    province = get_province(market)
    print(f'  "{market}" -> "{province}"')

# 统计各省份的数据
province_data = {}
for market in markets:
    province = get_province(market)
    if province not in province_data:
        province_data[province] = 0
    cursor.execute('SELECT COUNT(*) FROM cleaned_price_data WHERE market_name = %s', (market,))
    province_data[province] += cursor.fetchone()[0]

print('\n各省份数据量:')
for province, count in sorted(province_data.items(), key=lambda x: x[1], reverse=True):
    print(f'  {province}: {count}条')

conn.close()