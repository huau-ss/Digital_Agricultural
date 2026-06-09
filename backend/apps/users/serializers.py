from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from .models import CustomUser, SystemMessage


class UserRegistrationSerializer(serializers.ModelSerializer):
    """用户注册序列化器"""
    # 定义密码字段，使用 Django 内置的密码验证器
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],     # Django 密码强度验证
        style={'input_type': 'password'}
    )
    # 定义确认密码字段，用于确认密码
    password_confirm = serializers.CharField(
        write_only=True,   # 只写入，不返回给前端
        required=True,
        style={'input_type': 'password'}
    )
    
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password', 'password_confirm', 'role', 'phone', 'address']
        # 定义额外参数，用于控制字段是否必填
        extra_kwargs = {
            'email': {'required': False},
            'role': {'required': False},
            'phone': {'required': False},
            'address': {'required': False},
        }
    
    # 验证密码是否一致
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password_confirm": "两次密码输入不一致"})
        return attrs
    
    # 创建用户
    def create(self, validated_data):
        validated_data.pop('password_confirm')   # 删除确认密码字段
        # 管理员注册时自动审核通过并赋予 staff 权限
        if validated_data.get('role') == 'admin':
            validated_data['is_staff'] = True
            validated_data['is_approved'] = True
        user = CustomUser.objects.create_user(**validated_data)   # 创建用户
        return user   # 返回创建的用户


class UserLoginSerializer(serializers.Serializer):
    """用户登录序列化器"""
    username = serializers.CharField(required=True)
    password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )
    
    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')

        user = authenticate(username=username, password=password)
        if not user:
            raise serializers.ValidationError("用户名或密码错误")
        if not user.is_active:
            raise serializers.ValidationError("用户已被禁用")
        if not user.is_approved:
            raise serializers.ValidationError("账号尚未通过管理员审核，请耐心等待")

        attrs['user'] = user
        return attrs


class UserSerializer(serializers.ModelSerializer):
    """用户信息序列化器"""
    role_display = serializers.CharField(source='get_role_display', read_only=True)

    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'role', 'role_display', 'phone', 'address',
                  'created_at', 'updated_at', 'is_active', 'is_approved']
        read_only_fields = ['id', 'created_at', 'updated_at']


class UserUpdateSerializer(serializers.ModelSerializer):
    """用户信息更新序列化器"""
    
    class Meta:
        model = CustomUser
        fields = ['email', 'phone', 'address']
    
    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class ChangePasswordSerializer(serializers.Serializer):
    """修改密码序列化器"""
    old_password = serializers.CharField(
        required=True,
        style={'input_type': 'password'}
    )
    new_password = serializers.CharField(
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    new_password_confirm = serializers.CharField(
        required=True,
        style={'input_type': 'password'}
    )
    
    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("原密码错误")
        return value
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({"new_password_confirm": "两次新密码输入不一致"})
        return attrs
    
    def save(self):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class SystemMessageSerializer(serializers.ModelSerializer):
    """系统消息序列化器"""
    message_type_display = serializers.CharField(source='get_message_type_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    time_ago = serializers.SerializerMethodField()

    class Meta:
        model = SystemMessage
        fields = [
            'id', 'title', 'content', 'message_type', 'message_type_display',
            'priority', 'priority_display', 'is_read', 'related_product_id',
            'related_product_name', 'price_change_percent', 'created_at',
            'read_at', 'time_ago',
            # 价格预警详细信息
            'current_price', 'predicted_price', 'change_direction', 'change_days'
        ]
        read_only_fields = ['id', 'created_at', 'read_at']

    def get_time_ago(self, obj):
        """计算相对时间"""
        from django.utils import timezone
        from django.utils.timesince import timesince
        return timesince(obj.created_at, timezone.now())


class AdminUserListSerializer(serializers.ModelSerializer):
    """管理员用户列表序列化器"""
    role_display = serializers.CharField(source='get_role_display', read_only=True)

    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'email', 'role', 'role_display',
            'phone', 'address', 'is_active', 'is_approved',
            'is_staff', 'last_login', 'created_at', 'updated_at'
        ]


class AdminUserActionSerializer(serializers.Serializer):
    """管理员操作用户序列化器"""
    user_id = serializers.IntegerField(required=True)
    action = serializers.ChoiceField(
        choices=['enable', 'disable', 'approve', 'reject'],
        required=True
    )

    def validate(self, attrs):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        try:
            user = User.objects.get(id=attrs['user_id'])
        except User.DoesNotExist:
            raise serializers.ValidationError({'user_id': '用户不存在'})

        attrs['user'] = user
        return attrs
