from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    ordering = ['email']
    list_display = ['email', 'first_name', 'last_name', 'stato', 'is_staff', 'is_active']
    list_filter = ['stato', 'is_staff', 'is_active', 'roles']
    search_fields = ['email', 'first_name', 'last_name']
    filter_horizontal = ['roles', 'groups', 'user_permissions']

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Dati personali', {'fields': ('first_name', 'last_name', 'stato')}),
        (
            'Ruoli e permessi',
            {
                'fields': (
                    'roles',
                    'is_active',
                    'is_staff',
                    'is_superuser',
                    'groups',
                    'user_permissions',
                )
            },
        ),
        ('Date importanti', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (
            None,
            {
                'classes': ('wide',),
                'fields': ('email', 'password1', 'password2'),
            },
        ),
    )
