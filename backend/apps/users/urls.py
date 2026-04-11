from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    UserRegistrationView,
    UserLoginView,
    UserLogoutView,
    UserProfileView,
    ChangePasswordView,
    MessageListView,
    MessageUnreadCountView,
    MessageMarkReadView,
    MessageDeleteView,
)

app_name = 'users'

urlpatterns = [
    path('register/', UserRegistrationView.as_view(), name='register'),
    path('login/', UserLoginView.as_view(), name='login'),
    path('logout/', UserLogoutView.as_view(), name='logout'),
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    # 消息相关
    path('messages/', MessageListView.as_view(), name='messages'),
    path('messages/unread-count/', MessageUnreadCountView.as_view(), name='messages-unread-count'),
    path('messages/mark-read/', MessageMarkReadView.as_view(), name='messages-mark-read'),
    path('messages/delete/', MessageDeleteView.as_view(), name='messages-delete'),
]
