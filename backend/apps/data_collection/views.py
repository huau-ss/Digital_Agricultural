from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
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
