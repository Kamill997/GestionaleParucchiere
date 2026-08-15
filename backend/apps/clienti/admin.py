from django.contrib import admin

from .models import Cliente


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ['nome', 'email', 'telefono', 'bloccato', 'contatore_no_show']
    list_filter = ['bloccato']
    search_fields = ['nome', 'email', 'telefono']
    autocomplete_fields = ['user']
