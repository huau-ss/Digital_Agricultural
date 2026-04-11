from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from django.db.models import Q
from .serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    UserSerializer,
    UserUpdateSerializer,
    ChangePasswordSerializer,
    SystemMessageSerializer
)
from .models import SystemMessage


class UserRegistrationView(generics.CreateAPIView):
    """用户注册"""
    permission_classes = [AllowAny]
    serializer_class = UserRegistrationSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'code': 201,
            'message': '注册成功',
            'data': {
                'user': UserSerializer(user).data,
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }
            }
        }, status=status.HTTP_201_CREATED)


class UserLoginView(APIView):
    """用户登录"""
    permission_classes = [AllowAny]
    serializer_class = UserLoginSerializer
    
    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'code': 200,
            'message': '登录成功',
            'data': {
                'user': UserSerializer(user).data,
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }
            }
        }, status=status.HTTP_200_OK)


class UserLogoutView(APIView):
    """用户登出"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if refresh_token:
                try:
                    token = RefreshToken(refresh_token)
                    token.blacklist()
                except Exception:
                    pass
            return Response({
                'code': 200,
                'message': '登出成功'
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'code': 200,
                'message': '登出成功'
            }, status=status.HTTP_200_OK)


class UserProfileView(generics.RetrieveUpdateAPIView):
    """获取和更新个人信息"""
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return UserUpdateSerializer
        return UserSerializer
    
    def retrieve(self, request, *args, **kwargs):
        serializer = self.get_serializer(request.user)
        return Response({
            'code': 200,
            'message': '获取成功',
            'data': serializer.data
        }, status=status.HTTP_200_OK)
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        serializer = self.get_serializer(request.user, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response({
            'code': 200,
            'message': '更新成功',
            'data': UserSerializer(request.user).data
        }, status=status.HTTP_200_OK)


class ChangePasswordView(APIView):
    """修改密码"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({
            'code': 200,
            'message': '密码修改成功'
        }, status=status.HTTP_200_OK)


class MessageListView(generics.ListAPIView):
    """获取用户消息列表"""
    permission_classes = [IsAuthenticated]
    serializer_class = SystemMessageSerializer

    def get_queryset(self):
        queryset = SystemMessage.objects.filter(user=self.request.user)

        # 按类型筛选
        message_type = self.request.query_params.get('type')
        if message_type:
            queryset = queryset.filter(message_type=message_type)

        # 按是否已读筛选
        is_read = self.request.query_params.get('is_read')
        if is_read is not None:
            queryset = queryset.filter(is_read=is_read.lower() == 'true')

        return queryset.order_by('-created_at')

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'code': 200,
            'message': '获取成功',
            'data': serializer.data
        })


class MessageUnreadCountView(APIView):
    """获取未读消息数量"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        count = SystemMessage.objects.filter(
            user=request.user,
            is_read=False
        ).count()

        return Response({
            'code': 200,
            'message': '获取成功',
            'data': {'unread_count': count}
        })


class MessageMarkReadView(APIView):
    """标记消息为已读"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        message_id = request.data.get('message_id')

        if message_id:
            # 标记单条消息
            try:
                message = SystemMessage.objects.get(id=message_id, user=request.user)
                message.mark_as_read()
                return Response({
                    'code': 200,
                    'message': '已标记为已读'
                })
            except SystemMessage.DoesNotExist:
                return Response({
                    'code': 404,
                    'message': '消息不存在'
                }, status=status.HTTP_404_NOT_FOUND)
        else:
            # 标记所有消息为已读
            SystemMessage.objects.filter(
                user=request.user,
                is_read=False
            ).update(is_read=True)

            from django.utils import timezone
            SystemMessage.objects.filter(
                user=request.user,
                is_read=True,
                read_at__isnull=True
            ).update(read_at=timezone.now())

            return Response({
                'code': 200,
                'message': '已标记全部已读'
            })


class MessageDeleteView(APIView):
    """删除消息"""
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        message_id = request.data.get('message_id')

        try:
            message = SystemMessage.objects.get(id=message_id, user=request.user)
            message.delete()
            return Response({
                'code': 200,
                'message': '删除成功'
            })
        except SystemMessage.DoesNotExist:
            return Response({
                'code': 404,
                'message': '消息不存在'
            }, status=status.HTTP_404_NOT_FOUND)
