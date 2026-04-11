from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'role', 'role_display', 'is_active', 'created_at']
    list_filter = ['role', 'is_active', 'is_staff']
    search_fields = ['username', 'email', 'phone']
    ordering = ['-created_at']
    
    fieldsets = UserAdmin.fieldsets + (
        ('扩展信息', {'fields': ('role', 'phone', 'address')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('扩展信息', {'fields': ('role', 'phone', 'address')}),
    )
    
    def role_display(self, obj):
        return obj.get_role_display()
    role_display.short_description = '角色名称'
