from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """Sola lettura: un log di audit non va modificato/creato a mano
    dall'interfaccia admin, solo consultato."""

    list_display = ['creato_il', 'user', 'azione', 'entita_coinvolta']
    list_filter = ['azione', 'entita_coinvolta']
    search_fields = ['azione', 'entita_coinvolta', 'user__email']
    readonly_fields = ['id', 'user', 'azione', 'entita_coinvolta', 'dettagli', 'creato_il']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
