from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .models import TradeInfo
from .serializers import TradeInfoSerializer


class TradeInfoViewSet(viewsets.ModelViewSet):
    """供需信息视图集"""
    serializer_class = TradeInfoSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['info_type', 'status', 'product', 'publisher']

    def get_queryset(self):
        return TradeInfo.objects.select_related('publisher', 'product').all()

    def perform_create(self, serializer):
        serializer.save(publisher=self.request.user)

    @action(detail=False, methods=['get'])
    def my_posts(self, request):
        """获取当前用户发布的信息"""
        queryset = self.get_queryset().filter(publisher=request.user)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """标记为已成交"""
        trade_info = self.get_object()
        if trade_info.publisher != request.user:
            return Response({'error': '无权限操作'}, status=status.HTTP_403_FORBIDDEN)
        trade_info.status = 'completed'
        trade_info.save()
        return Response({'message': '已标记为成交'})

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """取消信息"""
        trade_info = self.get_object()
        if trade_info.publisher != request.user:
            return Response({'error': '无权限操作'}, status=status.HTTP_403_FORBIDDEN)
        trade_info.status = 'cancelled'
        trade_info.save()
        return Response({'message': '已取消'})
