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
    SystemMessageSerializer,
    AdminUserListSerializer,
    AdminUserActionSerializer,
)
from .models import CustomUser, SystemMessage


class UserRegistrationView(generics.CreateAPIView):
    """用户注册"""
    permission_classes = [AllowAny]   # 允许任何用户访问
    serializer_class = UserRegistrationSerializer   # 使用用户注册序列化器
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # 注册后不发放 token，需要管理员审核后再登录获取 token
        return Response({
            'code': 201,
            'message': '注册成功，请等待管理员审核后登录',
            'data': {
                'user_id': user.id,
                'username': user.username,
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
        refresh = RefreshToken.for_user(user)       # 生成刷新令牌
        
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

        # 按类型筛选（支持 type 或 message_type）
        message_type = self.request.query_params.get('type') or self.request.query_params.get('message_type')
        if message_type:
            queryset = queryset.filter(message_type=message_type)

        # 按优先级筛选
        priority = self.request.query_params.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)

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
        queryset = SystemMessage.objects.filter(user=request.user, is_read=False)

        # 按类型筛选
        message_type = request.query_params.get('message_type')
        if message_type:
            queryset = queryset.filter(message_type=message_type)

        count = queryset.count()

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
        message_type = request.data.get('message_type')  # 用于标记特定类型的所有消息

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
        elif message_type:
            # 标记特定类型的所有消息为已读
            queryset = SystemMessage.objects.filter(
                user=request.user,
                message_type=message_type,
                is_read=False
            )
            count = queryset.count()
            queryset.update(is_read=True)

            from django.utils import timezone
            SystemMessage.objects.filter(
                user=request.user,
                message_type=message_type,
                is_read=True,
                read_at__isnull=True
            ).update(read_at=timezone.now())

            return Response({
                'code': 200,
                'message': f'已标记 {count} 条消息为已读'
            })
        else:
            # 标记所有消息为已读
            queryset = SystemMessage.objects.filter(
                user=request.user,
                is_read=False
            )
            count = queryset.count()
            queryset.update(is_read=True)

            from django.utils import timezone
            SystemMessage.objects.filter(
                user=request.user,
                is_read=True,
                read_at__isnull=True
            ).update(read_at=timezone.now())

            return Response({
                'code': 200,
                'message': f'已标记 {count} 条消息为已读'
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


# ==================== 管理员用户管理 API ====================

class AdminUserListView(generics.ListAPIView):
    """管理员 - 用户列表"""
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        return AdminUserListSerializer

    def get_queryset(self):
        queryset = CustomUser.objects.all().order_by('-created_at')

        role = self.request.query_params.get('role')
        is_active = self.request.query_params.get('is_active')
        is_approved = self.request.query_params.get('is_approved')
        search = self.request.query_params.get('search')

        if role:
            queryset = queryset.filter(role=role)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        if is_approved is not None:
            queryset = queryset.filter(is_approved=is_approved.lower() == 'true')
        if search:
            queryset = queryset.filter(
                Q(username__icontains=search) |
                Q(email__icontains=search) |
                Q(phone__icontains=search)
            )

        return queryset

    def list(self, request, *args, **kwargs):
        # 仅限管理员
        if not request.user.is_staff and request.user.role != 'admin':
            return Response({'code': 403, 'message': '无权限'}, status=status.HTTP_403_FORBIDDEN)

        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response({'code': 200, 'message': '获取成功', 'data': serializer.data})


class AdminUserStatsView(APIView):
    """管理员 - 用户统计"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.is_staff and request.user.role != 'admin':
            return Response({'code': 403, 'message': '无权限'}, status=status.HTTP_403_FORBIDDEN)

        total = CustomUser.objects.count()
        active = CustomUser.objects.filter(is_active=True).count()
        pending = CustomUser.objects.filter(is_approved=False).count()
        farmer_count = CustomUser.objects.filter(role='farmer').count()
        buyer_count = CustomUser.objects.filter(role='buyer').count()
        admin_count = CustomUser.objects.filter(role='admin').count()

        return Response({
            'code': 200,
            'message': '获取成功',
            'data': {
                'total': total,
                'active': active,
                'inactive': total - active,
                'pending_approval': pending,
                'farmer_count': farmer_count,
                'buyer_count': buyer_count,
                'admin_count': admin_count,
            }
        })


class AdminUserActionView(APIView):
    """管理员 - 用户操作（启用/禁用/审核通过/拒绝）"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not request.user.is_staff and request.user.role != 'admin':
            return Response({'code': 403, 'message': '无权限'}, status=status.HTTP_403_FORBIDDEN)

        serializer = AdminUserActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']
        action = serializer.validated_data['action']

        # 禁止管理员操作自己
        if user.id == request.user.id:
            return Response({'code': 400, 'message': '不能对自己执行此操作'}, status=status.HTTP_400_BAD_REQUEST)

        msg = ''
        if action == 'enable':
            user.is_active = True
            user.save(update_fields=['is_active'])
            msg = f'已启用用户 {user.username}'
        elif action == 'disable':
            user.is_active = False
            user.save(update_fields=['is_active'])
            msg = f'已禁用用户 {user.username}'
        elif action == 'approve':
            user.is_approved = True
            user.is_active = True
            user.save(update_fields=['is_approved', 'is_active'])
            msg = f'已通过用户 {user.username} 的审核'
        elif action == 'reject':
            user.is_active = False
            user.is_approved = False
            user.save(update_fields=['is_active', 'is_approved'])
            msg = f'已拒绝用户 {user.username}'

        return Response({'code': 200, 'message': msg})
