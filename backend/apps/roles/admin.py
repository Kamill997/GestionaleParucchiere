from django.contrib import admin

from .models import Permission, Role


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ['nome']
    search_fields = ['nome']
    filter_horizontal = ['permissions']


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ['chiave']
    search_fields = ['chiave']
