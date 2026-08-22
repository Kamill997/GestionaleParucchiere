from django.contrib import admin

from .models import Notifica


@admin.register(Notifica)
class NotificaAdmin(admin.ModelAdmin):
    """Sola lettura: una notifica non va creata/modificata a mano
    dall'interfaccia admin (stesso pattern di AuditLog), solo consultata
    per debug."""

    list_display = ['creato_il', 'destinatario', 'tipo', 'titolo', 'letta']
    list_filter = ['tipo', 'letta']
    search_fields = ['titolo', 'messaggio', 'destinatario__email']
    readonly_fields = ['id', 'destinatario', 'tipo', 'titolo', 'messaggio', 'link', 'creato_il']

    def has_add_permission(self, request):
        return False
