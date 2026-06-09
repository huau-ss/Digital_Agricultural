from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Avg, Max, Min, Sum, Count, Q as ModelQ
from datetime import datetime, timedelta
from .models import AgriculturalProduct, CleanedPriceData
from .serializers import CleanedPriceDataSerializer

# 市场到省份映射
MARKET_PROVINCE_MAP = {
    'Beijing Xinfadi': '北京',
    '北京新发地批发市场': '北京',
    '上海农产品中心批发市场': '上海',
    'Shanghai Agrip': '上海',
    '广州江南果菜批发市场': '广东',
    '深圳海吉星农产品物流园': '广东',
    '南京农副产品物流中心': '江苏',
    '南京众彩物流配送中心': '江苏',
    '南京众彩市场': '江苏',
    '杭州果品批发交易市场': '浙江',
    '杭州勾庄农副产品物流中心': '浙江',
    '杭州勾庄市场': '浙江',
    '武汉白沙洲农副产品大市场': '湖北',
    '武汉白沙洲': '湖北',
    '成都农产品中心批发市场': '四川',
    '成都龙泉聚和果蔬交易中心': '四川',
    '重庆双福国际农贸城': '重庆',
    '重庆双福': '重庆',
    '郑州万邦国际农产品物流城': '河南',
    '郑州万邦': '河南',
    '长沙红星农副产品大市场': '湖南',
    '长沙红星': '湖南',
    '西安欣桥农产品物流中心': '陕西',
    '西安摩尔农产品有限责任公司': '陕西',
    '西安摩尔': '陕西',
    '哈尔滨润恒城农产品批发市场': '黑龙江',
    '哈尔滨润恒': '黑龙江',
    '沈阳八家子批发市场': '辽宁',
    '沈阳八家子': '辽宁',
    '山东匡山农产品综合交易市场': '山东',
    '山东匡山': '山东',
    '天津金钟农产品批发市场': '天津',
    '天津金钟': '天津',
    '石家庄桥西蔬菜中心批发市场': '河北',
    '石家庄桥西': '河北',
    '南昌深圳农产品中心批发市场': '江西',
    '南昌深圳': '江西',
    '福州海峡农产品批发市场': '福建',
    '福州海峡': '福建',
    '厦门闽南农副产品物流中心': '福建',
    '厦门闽南': '福建',
    '昆明龙城农产品批发市场': '云南',
    '昆明龙城': '云南',
    '贵阳农产品物流园': '贵州',
    '贵阳农产品': '贵州',
    '兰州毅和农产品市场': '甘肃',
    '兰州毅和': '甘肃',
    '乌鲁木齐北园春农贸市场': '新疆',
    '乌鲁木齐北园春': '新疆',
    '合肥周谷堆农产品批发市场': '安徽',
    '合肥周谷堆': '安徽',
    '太原市河西农产品有限公司': '山西',
    '太原河西': '山西',
    '呼和浩特馨昊佳农产品': '内蒙古',
    '呼和浩特馨昊': '内蒙古',
    '南宁农产品交易中心': '广西',
    '南宁农产品': '广西',
    '海口南北水果市场': '海南',
    '海口南北': '海南',
}


# 省份名称标准化映射（简称 -> ECharts地图中的完整名称）
PROVINCE_FULL_NAMES = {
    '北京': '北京市',
    '上海': '上海市',
    '天津': '天津市',
    '重庆': '重庆市',
    '广东': '广东省',
    '河南': '河南省',
    '湖南': '湖南省',
    '陕西': '陕西省',
    '重庆': '重庆市',
    '四川': '四川省',
    '江苏': '江苏省',
    '浙江': '浙江省',
    '湖北': '湖北省',
    '山东': '山东省',
    '辽宁': '辽宁省',
    '黑龙江': '黑龙江省',
    '河北': '河北省',
    '安徽': '安徽省',
    '福建': '福建省',
    '江西': '江西省',
    '云南': '云南省',
    '贵州': '贵州省',
    '甘肃': '甘肃省',
    '新疆': '新疆维吾尔自治区',
    '山西': '山西省',
    '内蒙古': '内蒙古自治区',
    '广西': '广西壮族自治区',
    '海南': '海南省',
    '青海': '青海省',
    '西藏': '西藏自治区',
    '宁夏': '宁夏回族自治区',
    '吉林': '吉林省',
    '台湾': '台湾省',
    '香港': '香港特别行政区',
    '澳门': '澳门特别行政区',
}


def get_province_from_market(market_name):
    """从市场名称获取省份"""
    if market_name in MARKET_PROVINCE_MAP:
        return MARKET_PROVINCE_MAP[market_name]

    # 模糊匹配
    for key, province in MARKET_PROVINCE_MAP.items():
        if key in market_name or market_name in key:
            return province

    # 默认判断
    if '北京' in market_name:
        return '北京'
    elif '上海' in market_name:
        return '上海'
    elif '广东' in market_name or '广州' in market_name or '深圳' in market_name:
        return '广东'
    elif '江苏' in market_name or '南京' in market_name:
        return '江苏'
    elif '浙江' in market_name or '杭州' in market_name:
        return '浙江'
    elif '湖北' in market_name or '武汉' in market_name:
        return '湖北'
    elif '四川' in market_name or '成都' in market_name or '重庆' in market_name:
        return '四川'
    elif '河南' in market_name or '郑州' in market_name:
        return '河南'
    elif '山东' in market_name:
        return '山东'
    elif '湖南' in market_name or '长沙' in market_name:
        return '湖南'
    elif '陕西' in market_name or '西安' in market_name:
        return '陕西'
    elif '辽宁' in market_name or '沈阳' in market_name or '大连' in market_name:
        return '辽宁'
    elif '黑龙江' in market_name or '哈尔滨' in market_name:
        return '黑龙江'
    elif '天津' in market_name:
        return '天津'
    elif '河北' in market_name or '石家庄' in market_name:
        return '河北'
    elif '安徽' in market_name or '合肥' in market_name:
        return '安徽'
    elif '福建' in market_name or '福州' in market_name or '厦门' in market_name:
        return '福建'
    elif '江西' in market_name or '南昌' in market_name:
        return '江西'
    elif '云南' in market_name or '昆明' in market_name:
        return '云南'
    elif '贵州' in market_name or '贵阳' in market_name:
        return '贵州'
    elif '甘肃' in market_name or '兰州' in market_name:
        return '甘肃'
    elif '新疆' in market_name or '乌鲁木齐' in market_name:
        return '新疆'
    elif '山西' in market_name or '太原' in market_name:
        return '山西'
    elif '内蒙古' in market_name or '呼和浩特' in market_name:
        return '内蒙古'
    elif '广西' in market_name or '南宁' in market_name:
        return '广西'
    elif '海南' in market_name or '海口' in market_name:
        return '海南'

    return '其他'


def normalize_province_name(province_name):
    """将省份简称转换为 ECharts 地图中的完整名称"""
    return PROVINCE_FULL_NAMES.get(province_name, province_name)


class VisualizationViewSet(viewsets.ViewSet):
    """可视化数据视图集"""

    def list(self, request):
        """获取所有可用产品列表，按最近180天数据量排序"""
        today = datetime.now().date()
        # 使用180天确保能查到历史数据
        query_days = 180
        start_date = today - timedelta(days=query_days)

        from django.db.models import Count

        products = AgriculturalProduct.objects.filter(is_active=True).annotate(
            recent_count=Count('price_history', filter=ModelQ(price_history__date__gte=start_date))
        ).values('id', 'name', 'category', 'recent_count').order_by('-recent_count', 'id')

        return Response(list(products))

    @action(detail=False, methods=['get'])
    def price_trend(self, request):
        """
        获取近N天价格走势数据
        用于 ECharts 折线图

        参数:
            product_id: 产品ID (必需)
            days: 天数，默认30天
        """
        product_id = request.query_params.get('product_id')
        days = int(request.query_params.get('days', 30))

        if not product_id:
            return Response({'error': 'product_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)

        # 使用原始数据表 PriceHistory（数据更完整）
        from apps.data_collection.models import PriceHistory

        queryset = PriceHistory.objects.filter(
            product_id=product_id,
            date__gte=start_date,
            date__lte=end_date
        ).values('date', 'avg_price').order_by('date')

        # 按日期分组，计算每日平均价格
        daily_data = {}
        for item in queryset:
            date_str = item['date'].strftime('%Y-%m-%d')
            if date_str not in daily_data:
                daily_data[date_str] = []
            daily_data[date_str].append(float(item['avg_price']))

        # 构建 ECharts 格式数据
        dates = sorted(daily_data.keys())
        prices = [round(sum(daily_data[d]) / len(daily_data[d]), 2) for d in dates]

        # 获取产品信息
        try:
            product = AgriculturalProduct.objects.get(id=product_id)
            product_name = product.name
            category = product.category
        except AgriculturalProduct.DoesNotExist:
            product_name = '未知'
            category = 'unknown'

        return Response({
            'product_id': int(product_id),
            'product_name': product_name,
            'category': category,
            'days': days,
            'dates': dates,
            'prices': prices,
            'data': [
                {'date': d, 'price': p}
                for d, p in zip(dates, prices)
            ]
        })

    @action(detail=False, methods=['get'])
    def price_trend_by_market(self, request):
        """
        获取按市场分组的价格走势
        """
        from apps.data_collection.models import PriceHistory

        product_id = request.query_params.get('product_id')
        days = int(request.query_params.get('days', 30))

        if not product_id:
            return Response({'error': 'product_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)

        queryset = PriceHistory.objects.filter(
            product_id=product_id,
            date__gte=start_date,
            date__lte=end_date
        ).values('date', 'avg_price', 'market_name').order_by('date', 'market_name')

        # 按市场分组
        market_data = {}
        for item in queryset:
            market = item['market_name']
            date_str = item['date'].strftime('%Y-%m-%d')
            if market not in market_data:
                market_data[market] = {'dates': set(), 'prices': []}
            market_data[market]['dates'].add(date_str)

        # 获取所有日期
        all_dates = set()
        for item in queryset:
            all_dates.add(item['date'].strftime('%Y-%m-%d'))
        all_dates = sorted(all_dates)

        # 构建每个市场的数据
        result = []
        for market, data in market_data.items():
            market_queryset = PriceHistory.objects.filter(
                product_id=product_id,
                market_name=market,
                date__gte=start_date,
                date__lte=end_date
            ).values('date', 'avg_price').order_by('date')

            daily_prices = {}
            for item in market_queryset:
                daily_prices[item['date'].strftime('%Y-%m-%d')] = float(item['avg_price'])

            prices = [daily_prices.get(d, None) for d in all_dates]

            result.append({
                'market': market,
                'dates': all_dates,
                'prices': prices
            })

        return Response({
            'product_id': int(product_id),
            'dates': all_dates,
            'markets': result
        })

    @action(detail=False, methods=['get'])
    def province_heatmap(self, request):
        """
        获取省份热力图数据
        用于 ECharts 中国地图
        """
        from apps.data_collection.models import PriceHistory

        product_id = request.query_params.get('product_id')
        days = int(request.query_params.get('days', 30))

        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)

        queryset = PriceHistory.objects.filter(
            date__gte=start_date,
            date__lte=end_date
        )

        if product_id:
            queryset = queryset.filter(product_id=product_id)

        # 聚合数据
        data = queryset.values('market_name', 'avg_price').annotate(
            count=Count('id'),
            max_p=Max('avg_price'),
            min_p=Min('avg_price')
        )

        # 按省份分组
        province_data = {}
        for item in data:
            province = get_province_from_market(item['market_name'])
            if province not in province_data:
                province_data[province] = []
            province_data[province].append(float(item['avg_price']))

        # 计算每个省份的平均价格
        province_avg = {}
        for province, prices in province_data.items():
            if prices:
                province_avg[province] = round(sum(prices) / len(prices), 2)

        # 转换为 ECharts 地图格式（使用标准化省份名称）
        map_data = [
            {'name': normalize_province_name(province), 'value': avg_price}
            for province, avg_price in province_avg.items()
        ]

        # 按价格排序
        map_data.sort(key=lambda x: x['value'], reverse=True)

        return Response({
            'days': days,
            'province_data': province_avg,
            'map_data': map_data,
            'statistics': {
                'province_count': len(province_avg),
                'max_price': max(province_avg.values()) if province_avg else None,
                'min_price': min(province_avg.values()) if province_avg else None,
                'avg_price': round(sum(province_avg.values()) / len(province_avg), 2) if province_avg else None
            }
        })

    @action(detail=False, methods=['get'])
    def product_comparison(self, request):
        """
        获取多产品价格对比
        """
        from apps.data_collection.models import PriceHistory

        product_ids = request.query_params.get('product_ids', '')
        days = int(request.query_params.get('days', 30))

        if product_ids:
            product_ids = [int(x) for x in product_ids.split(',')]
        else:
            # 默认取前5个产品
            product_ids = list(AgriculturalProduct.objects.filter(is_active=True).values_list('id', flat=True)[:5])

        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)

        result = []
        for pid in product_ids:
            try:
                product = AgriculturalProduct.objects.get(id=pid)
                avg_price = PriceHistory.objects.filter(
                    product_id=pid,
                    date__gte=start_date,
                    date__lte=end_date
                ).aggregate(avg=Avg('avg_price'))['avg']

                result.append({
                    'product_id': pid,
                    'product_name': product.name,
                    'category': product.category,
                    'avg_price': round(float(avg_price), 2) if avg_price else None
                })
            except AgriculturalProduct.DoesNotExist:
                continue

        return Response(result)

    @action(detail=False, methods=['get'])
    def region_comparison(self, request):
        """
        获取同一产品在不同地区的价格对比
        """
        product_id = request.query_params.get('product_id')
        days = int(request.query_params.get('days', 30))

        if not product_id:
            return Response({'error': 'product_id 是必需参数'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            product_id = int(product_id)
            product = AgriculturalProduct.objects.get(id=product_id)
        except (ValueError, AgriculturalProduct.DoesNotExist):
            return Response({'error': '无效的 product_id'}, status=status.HTTP_400_BAD_REQUEST)

        start_date = datetime.now().date() - timedelta(days=days)

        # 按市场分组计算平均价格
        market_data = CleanedPriceData.objects.filter(
            product_id=product_id,
            date__gte=start_date
        ).values('market_name').annotate(
            market_avg=Avg('avg_price'),
            market_max=Max('avg_price'),
            market_min=Min('avg_price'),
            count=Count('id')
        ).order_by('-market_avg')

        # 提取省份信息
        result = []
        for item in market_data:
            province = get_province_from_market(item['market_name'])
            result.append({
                'market_name': item['market_name'],
                'province': province,
                'avg_price': round(float(item['market_avg']), 2) if item['market_avg'] else None,
                'max_price': round(float(item['market_max']), 2) if item['market_max'] else None,
                'min_price': round(float(item['market_min']), 2) if item['market_min'] else None,
                'record_count': item['count']
            })

        return Response({
            'product_id': product_id,
            'product_name': product.name,
            'data': result
        })

    @action(detail=False, methods=['get'])
    def dashboard_summary(self, request):
        """
        获取仪表盘摘要数据
        """
        today = datetime.now().date()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)

        # 基本统计
        total_records = CleanedPriceData.objects.count()
        total_products = AgriculturalProduct.objects.filter(is_active=True).count()

        # 获取有数据的省份数
        markets = CleanedPriceData.objects.values('market_name').distinct()
        provinces = set()
        for m in markets:
            provinces.add(get_province_from_market(m['market_name']))

        # 近7天数据量
        week_records = CleanedPriceData.objects.filter(date__gte=week_ago).count()

        # 价格统计
        price_stats = CleanedPriceData.objects.aggregate(
            avg=Avg('avg_price'),
            max=Max('avg_price'),
            min=Min('avg_price')
        )

        # 异常值统计
        outlier_count = CleanedPriceData.objects.filter(is_outlier=True).count()

        # 价格趋势（近30天）
        daily_stats = CleanedPriceData.objects.filter(
            date__gte=month_ago
        ).values('date').annotate(avg_price=Avg('avg_price')).order_by('date')

        trend_data = [
            {
                'date': item['date'].strftime('%Y-%m-%d'),
                'avg_price': round(float(item['avg_price']), 2)
            }
            for item in daily_stats
        ]

        return Response({
            'summary': {
                'total_records': total_records,
                'total_products': total_products,
                'province_count': len(provinces),
                'week_records': week_records,
                'outlier_count': outlier_count,
                'price_avg': round(float(price_stats['avg']), 2) if price_stats['avg'] else None,
                'price_max': round(float(price_stats['max']), 2) if price_stats['max'] else None,
                'price_min': round(float(price_stats['min']), 2) if price_stats['min'] else None,
            },
            'trend': trend_data
        })
