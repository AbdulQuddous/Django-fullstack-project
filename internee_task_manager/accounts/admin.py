from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'full_name', 'email', 'role', 'is_active', 'created_at']
    list_filter = ['role', 'is_active']
    search_fields = ['username', 'full_name', 'email']
    fieldsets = UserAdmin.fieldsets + (
        ('Profile Info', {'fields': ('full_name', 'role', 'profile_picture', 'bio', 'phone')}),
    )
