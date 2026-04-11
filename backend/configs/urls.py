"""
URL Configuration for Digital Agriculture Project
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # 用户认证路由
    path('api/auth/', include('apps.users.urls')),

    # 应用路由
    path('api/home/', include('apps.home.urls')),
    path('api/data-collection/', include('apps.data_collection.urls')),
    path('api/data-analysis/', include('apps.data_analysis.urls')),
    path('api/decision-support/', include('apps.decision_support.urls')),
]

# 配置媒体文件和静态文件的访问
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
