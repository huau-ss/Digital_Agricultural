"""
自定义认证类：JWT 认证 + 检查账号是否通过审核
"""
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, AuthenticationFailed


class ApprovedUserJWTAuthentication(JWTAuthentication):
    """
    JWT 认证，仅允许 is_approved=True 的用户通过认证。
    不影响登录接口（登录在 UserLoginView 中手动校验），
    也不影响注册接口（注册是 AllowAny）。
    """

    def get_user(self, validated_token):
        user = super().get_user(validated_token)
        if user and not user.is_approved:
            raise AuthenticationFailed('账号尚未通过管理员审核，请耐心等待')
        return user
