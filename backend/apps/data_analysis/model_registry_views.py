# -*- coding: utf-8 -*-
"""
模型管理 API - 查看所有产品专用 LSTM 模型的训练状态和评估指标
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
import os
import joblib
import numpy as np
from apps.data_collection.models import AgriculturalProduct
from apps.data_analysis.lstm_service import MODEL_DIR


def _is_admin(request):
    return request.user.is_staff or request.user.role == 'admin'


def get_model_path(product_id):
    return os.path.join(MODEL_DIR, f'lstm_p{product_id}.pth')


def get_scaler_path(product_id):
    return os.path.join(MODEL_DIR, f'scaler_p{product_id}.pkl')


def get_registry_path():
    return os.path.join(MODEL_DIR, 'model_registry.pkl')


def get_model_info_for_product(product_id):
    """获取单个产品的模型信息"""
    model_path = get_model_path(product_id)
    scaler_path = get_scaler_path(product_id)

    info = {
        'product_id': product_id,
        'model_exists': os.path.exists(model_path),
        'scaler_exists': os.path.exists(scaler_path),
        'model_size_bytes': os.path.getsize(model_path) if os.path.exists(model_path) else 0,
        'metrics': None,
    }

    # 尝试从 model_registry.pkl 读取训练指标
    registry_path = get_registry_path()
    if os.path.exists(registry_path):
        try:
            registry = joblib.load(registry_path)
            if str(product_id) in registry:
                info['metrics'] = registry[str(product_id)]
            elif product_id in registry:
                info['metrics'] = registry[product_id]
        except Exception:
            pass

    return info


class ModelRegistryView(APIView):
    """模型管理 - 获取所有产品的模型状态"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not _is_admin(request):
            return Response({'code': 403, 'message': '无权限'}, status=status.HTTP_403_FORBIDDEN)

        products = AgriculturalProduct.objects.filter(is_active=True).order_by('id')
        results = []
        trained_count = 0
        total_count = products.count()

        for product in products:
            info = get_model_info_for_product(product.id)
            info['product_name'] = product.name
            info['category'] = product.category
            if info['model_exists']:
                trained_count += 1
            results.append(info)

        # 总模型数量统计
        model_dir_files = os.listdir(MODEL_DIR) if os.path.exists(MODEL_DIR) else []
        pth_files = [f for f in model_dir_files if f.endswith('.pth')]

        return Response({
            'code': 200,
            'message': '获取成功',
            'data': {
                'total_products': total_count,
                'trained_models': trained_count,
                'untrained_products': total_count - trained_count,
                'models_on_disk': len(pth_files),
                'products': results,
            }
        })


class ModelDetailView(APIView):
    """模型管理 - 获取单个产品的模型详情"""
    permission_classes = [IsAuthenticated]

    def get(self, request, product_id):
        if not _is_admin(request):
            return Response({'code': 403, 'message': '无权限'}, status=status.HTTP_403_FORBIDDEN)

        try:
            product = AgriculturalProduct.objects.get(id=product_id)
        except AgriculturalProduct.DoesNotExist:
            return Response({'code': 404, 'message': '产品不存在'}, status=status.HTTP_404_NOT_FOUND)

        info = get_model_info_for_product(product_id)
        info['product_name'] = product.name
        info['category'] = product.category

        return Response({
            'code': 200,
            'message': '获取成功',
            'data': info
        })
