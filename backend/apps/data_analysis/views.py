# -*- coding: utf-8 -*-
"""
价格预测 API 视图
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .lstm_service import predict_product_price, LSTMPredictor, get_product_price_history
from apps.data_collection.models import AgriculturalProduct
import os


class PricePredictionView(APIView):
    """价格预测 API"""

    def get(self, request):
        """
        GET /api/data-analysis/prediction/?product_id=1&days=7

        参数:
            product_id: 农产品 ID（必需）
            days: 预测天数，默认 7

        返回:
            历史价格数据和未来预测价格
        """
        product_id = request.query_params.get('product_id')

        if not product_id:
            return Response(
                {'success': False, 'error': 'product_id 是必需参数'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            product_id = int(product_id)
        except ValueError:
            return Response(
                {'success': False, 'error': 'product_id 必须是整数'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 验证产品存在
        try:
            product = AgriculturalProduct.objects.get(id=product_id)
        except AgriculturalProduct.DoesNotExist:
            return Response(
                {'success': False, 'error': f'产品 ID {product_id} 不存在'},
                status=status.HTTP_404_NOT_FOUND
            )

        days = int(request.query_params.get('days', 7))
        days = min(days, 30)

        result = predict_product_price(product_id, future_days=days)

        if not result.get('success'):
            return Response(
                {'success': False, 'error': result.get('error', '预测失败')},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 添加产品信息
        result['product_name'] = product.name
        result['product_category'] = product.get_category_display()

        return Response(result)


class ProductListForPredictionView(APIView):
    """获取可预测的产品列表"""

    def get(self, request):
        """
        GET /api/data-analysis/prediction/products/

        返回有足够历史数据进行预测的产品列表
        """
        from datetime import datetime, timedelta
        from apps.data_collection.models import CleanedPriceData

        min_days = LSTMPredictor.SEQ_LENGTH + 5
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=90)

        # 查询有足够数据的 产品
        from django.db.models import Count
        products_with_data = CleanedPriceData.objects.filter(
            date__gte=start_date,
            date__lte=end_date,
            is_outlier=False
        ).values('product_id').annotate(
            count=Count('id')
        ).filter(count__gte=min_days)

        product_ids = [item['product_id'] for item in products_with_data]
        products = AgriculturalProduct.objects.filter(id__in=product_ids, is_active=True)

        data = []
        for p in products:
            data.append({
                'id': p.id,
                'name': p.name,
                'category': p.category,
                'category_display': p.get_category_display(),
                'origin': p.origin,
                'unit': p.unit
            })

        return Response({
            'success': True,
            'count': len(data),
            'products': data
        })


class ModelInfoView(APIView):
    """模型信息 API"""

    def get(self, request):
        """
        GET /api/data-analysis/prediction/model-info/

        返回当前模型的信息
        """
        model_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'models', 'lstm'
        )

        model_file = os.path.join(model_dir, 'lstm_model.pth')
        scaler_file = os.path.join(model_dir, 'scaler.pkl')

        import joblib
        from datetime import datetime

        info = {
            'success': True,
            'model': {
                'path': model_file,
                'exists': os.path.exists(model_file),
                'parameters': {
                    'seq_length': LSTMPredictor.SEQ_LENGTH,
                    'hidden_size': LSTMPredictor.HIDDEN_SIZE,
                    'num_layers': LSTMPredictor.NUM_LAYERS,
                    'dropout': LSTMPredictor.DROPOUT
                }
            },
            'scaler': {
                'path': scaler_file,
                'exists': os.path.exists(scaler_file)
            },
            'server_time': datetime.now().isoformat()
        }

        if os.path.exists(model_file):
            info['model']['size_bytes'] = os.path.getsize(model_file)

        if os.path.exists(scaler_file):
            info['scaler']['size_bytes'] = os.path.getsize(scaler_file)

        return Response(info)
