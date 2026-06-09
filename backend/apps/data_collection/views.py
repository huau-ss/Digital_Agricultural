from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, Avg, Max, Min, Sum
from .models import AgriculturalProduct, PriceHistory, CleanedPriceData
from .serializers import (
    AgriculturalProductSerializer,
    PriceHistorySerializer,
    CleanedPriceDataSerializer
)


class AgriculturalProductViewSet(viewsets.ModelViewSet):
    """农产品视图集"""
    queryset = AgriculturalProduct.objects.filter(is_active=True)
    serializer_class = AgriculturalProductSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category)
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(Q(name__icontains=search) | Q(origin__icontains=search))
        return queryset

    @action(detail=True, methods=['get'])
    def price_trend(self, request, pk=None):
        """获取指定产品的价格趋势"""
        product = self.get_object()
        queryset = CleanedPriceData.objects.filter(product=product).order_by('date')

        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)

        serializer = CleanedPriceDataSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        """获取指定产品的价格统计"""
        product = self.get_object()
        queryset = CleanedPriceData.objects.filter(product=product)

        stats = queryset.aggregate(
            avg_price=Avg('avg_price'),
            max_price=Max('max_price'),
            min_price=Min('min_price'),
            total_volume=Sum('volume')
        )
        record_count = queryset.count()
        outlier_count = queryset.filter(is_outlier=True).count()

        return Response({
            'product_id': product.id,
            'product_name': product.name,
            'record_count': record_count,
            'outlier_count': outlier_count,
            'clean_count': record_count - outlier_count,
            'avg_price': stats['avg_price'],
            'max_price': stats['max_price'],
            'min_price': stats['min_price'],
            'total_volume': stats['total_volume'],
        })


class PriceHistoryViewSet(viewsets.ModelViewSet):
    """历史价格视图集（原始数据）"""
    queryset = PriceHistory.objects.all()
    serializer_class = PriceHistorySerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        product_id = self.request.query_params.get('product_id')
        if product_id:
            queryset = queryset.filter(product_id=product_id)

        market_name = self.request.query_params.get('market_name')
        if market_name:
            queryset = queryset.filter(market_name__icontains=market_name)

        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)

        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(product__category=category)

        return queryset

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """获取价格历史统计信息"""
        queryset = self.get_queryset()
        total_count = queryset.count()

        stats = queryset.aggregate(
            avg_avg_price=Avg('avg_price'),
            max_avg_price=Max('max_price'),
            min_avg_price=Min('avg_price'),
            total_volume=Sum('volume')
        )

        product_count = queryset.values('product').distinct().count()
        market_count = queryset.values('market_name').distinct().count()

        return Response({
            'total_count': total_count,
            'product_count': product_count,
            'market_count': market_count,
            'avg_avg_price': stats['avg_avg_price'],
            'max_avg_price': stats['max_avg_price'],
            'min_avg_price': stats['min_avg_price'],
            'total_volume': stats['total_volume'],
        })


class CleanedPriceDataViewSet(viewsets.ModelViewSet):
    """清洗后价格数据视图集"""
    queryset = CleanedPriceData.objects.all()
    serializer_class = CleanedPriceDataSerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        product_id = self.request.query_params.get('product_id')
        if product_id:
            queryset = queryset.filter(product_id=product_id)

        market_name = self.request.query_params.get('market_name')
        if market_name:
            queryset = queryset.filter(market_name__icontains=market_name)

        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)

        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(product__category=category)

        is_outlier = self.request.query_params.get('is_outlier')
        if is_outlier is not None:
            queryset = queryset.filter(is_outlier=is_outlier.lower() == 'true')

        return queryset

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """获取清洗后数据统计信息"""
        queryset = self.get_queryset()
        total_count = queryset.count()
        outlier_count = queryset.filter(is_outlier=True).count()
        clean_count = total_count - outlier_count

        stats = queryset.aggregate(
            avg_avg_price=Avg('avg_price'),
            max_avg_price=Max('max_price'),
            min_avg_price=Min('avg_price'),
            total_volume=Sum('volume')
        )

        product_count = queryset.values('product').distinct().count()
        market_count = queryset.values('market_name').distinct().count()

        return Response({
            'total_count': total_count,
            'clean_count': clean_count,
            'outlier_count': outlier_count,
            'product_count': product_count,
            'market_count': market_count,
            'avg_avg_price': stats['avg_avg_price'],
            'max_avg_price': stats['max_avg_price'],
            'min_avg_price': stats['min_avg_price'],
            'total_volume': stats['total_volume'],
        })

    @action(detail=False, methods=['get'])
    def price_trend(self, request):
        """获取价格趋势数据"""
        product_id = request.query_params.get('product_id')
        market_name = request.query_params.get('market_name')

        if not product_id:
            return Response(
                {'error': 'product_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        queryset = self.get_queryset().filter(product_id=product_id)
        if market_name:
            queryset = queryset.filter(market_name=market_name)

        queryset = queryset.order_by('date')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def market_comparison(self, request):
        """获取不同市场价格对比"""
        product_id = request.query_params.get('product_id')
        if not product_id:
            return Response(
                {'error': 'product_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        queryset = self.get_queryset().filter(product_id=product_id)
        markets = queryset.values('market_name').distinct()

        result = []
        for market in markets:
            market_name = market['market_name']
            market_data = queryset.filter(market_name=market_name)

            stats = market_data.aggregate(
                avg_price=Avg('avg_price'),
                max_price=Max('max_price'),
                min_price=Min('min_price'),
                total_volume=Sum('volume')
            )
            record_count = market_data.count()

            result.append({
                'market_name': market_name,
                'record_count': record_count,
                'avg_price': stats['avg_price'],
                'max_price': stats['max_price'],
                'min_price': stats['min_price'],
                'total_volume': stats['total_volume'],
            })

        result.sort(key=lambda x: x['avg_price'] or 0, reverse=True)
        return Response(result)

    @action(detail=False, methods=['get'])
    def outliers(self, request):
        """获取所有异常值记录"""
        queryset = self.get_queryset().filter(is_outlier=True)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


# ==================== 管理员数据管理 API ====================

class TriggerDataCollectionView(APIView):
    """手动触发数据采集"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not request.user.is_staff and request.user.role != 'admin':
            return Response({'code': 403, 'message': '无权限'}, status=status.HTTP_403_FORBIDDEN)

        import logging
        logger = logging.getLogger('django')

        target_date_str = request.data.get('date')
        if target_date_str:
            from datetime import datetime
            try:
                target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()
            except ValueError:
                return Response({
                    'code': 400,
                    'message': '日期格式错误，请使用 YYYY-MM-DD',
                    'data': None
                }, status=status.HTTP_400_BAD_REQUEST)
        else:
            from datetime import date, timedelta
            target_date = date.today() - timedelta(days=1)

        logger.info(f"手动触发数据采集，目标日期: {target_date}")

        try:
            from scripts.crawl_daily import DailyCrawler
            crawler = DailyCrawler(dry_run=False)

            before_count = PriceHistory.objects.count()

            crawler.load_known_products()
            crawler.crawl_yesterday_data(target_date)

            after_count = PriceHistory.objects.count()
            added_count = after_count - before_count

            return Response({
                'code': 200,
                'message': '数据采集完成',
                'data': {
                    'target_date': str(target_date),
                    'products_processed': crawler.stats['products_processed'],
                    'prices_added': crawler.stats['prices_added'],
                    'new_records': added_count,
                    'errors': crawler.stats['errors'],
                }
            })
        except Exception as e:
            logger.error(f"数据采集失败: {e}")
            return Response({
                'code': 500,
                'message': f'采集失败: {str(e)}',
                'data': None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class TriggerDataCleaningView(APIView):
    """手动触发数据清洗"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not request.user.is_staff and request.user.role != 'admin':
            return Response({'code': 403, 'message': '无权限'}, status=status.HTTP_403_FORBIDDEN)

        from scripts.clean_price_data import PriceDataCleaner
        import logging
        logger = logging.getLogger('django')

        days_back = int(request.data.get('days_back', 30))
        product_id = request.data.get('product_id')

        logger.info(f"手动触发数据清洗... days_back={days_back}, product_id={product_id}")

        try:
            cleaner = PriceDataCleaner()
            stats = cleaner.clean(days_back=days_back, product_id=int(product_id) if product_id else None)

            return Response({
                'code': 200,
                'message': '数据清洗完成',
                'data': {
                    'processed': stats.get('total_processed', 0),
                    'duplicates_removed': stats.get('duplicates_removed', 0),
                    'outliers_marked': stats.get('outliers_marked', 0),
                    'cleaned_inserted': stats.get('cleaned_inserted', 0),
                    'cleaned_updated': stats.get('cleaned_updated', 0),
                    'errors': stats.get('errors', 0),
                }
            })
        except Exception as e:
            return Response({
                'code': 500,
                'message': f'清洗失败: {str(e)}',
                'data': None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
