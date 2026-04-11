# -*- coding: utf-8 -*-
"""
价格预警检测 API 视图
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status
from .price_warning import run_price_warning_check, check_single_product_warning
from apps.data_collection.models import AgriculturalProduct


class TriggerWarningCheckView(APIView):
    """手动触发价格预警检测"""
    permission_classes = [AllowAny]  # 可以限制为管理员权限

    def post(self, request):
        """
        POST /api/data-analysis/warning/check/
        触发所有产品的价格预警检测
        """
        try:
            count = run_price_warning_check()
            return Response({
                'code': 200,
                'message': '价格预警检测完成',
                'data': {'messages_generated': count}
            })
        except Exception as e:
            return Response({
                'code': 500,
                'message': f'检测失败: {str(e)}',
                'data': None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CheckProductWarningView(APIView):
    """检测单个产品的价格预警"""
    permission_classes = [AllowAny]

    def post(self, request):
        """
        POST /api/data-analysis/warning/check-product/
        Body: {"product_id": 1}
        """
        product_id = request.data.get('product_id')

        if not product_id:
            return Response({
                'code': 400,
                'message': 'product_id 是必需参数',
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            product_id = int(product_id)
        except ValueError:
            return Response({
                'code': 400,
                'message': 'product_id 必须是整数',
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)

        result = check_single_product_warning(product_id)

        if result.get('success'):
            return Response({
                'code': 200,
                'message': '检测完成',
                'data': result
            })
        else:
            return Response({
                'code': 400,
                'message': result.get('error', '检测失败'),
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)


class ListProductsForWarningView(APIView):
    """获取可检测预警的产品列表"""
    permission_classes = [AllowAny]

    def get(self, request):
        """
        GET /api/data-analysis/warning/products/
        """
        products = AgriculturalProduct.objects.filter(is_active=True).values(
            'id', 'name', 'category'
        )

        return Response({
            'code': 200,
            'message': '获取成功',
            'data': list(products)
        })
