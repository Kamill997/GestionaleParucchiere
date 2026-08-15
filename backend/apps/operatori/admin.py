from django.contrib import admin

from .models import Disponibilita, Operatore


@admin.register(Operatore)
class OperatoreAdmin(admin.ModelAdmin):
    list_display = ['nome', 'specializzazioni', 'attivo']
    list_filter = ['attivo']
    search_fields = ['nome', 'specializzazioni', 'user__email']
    autocomplete_fields = ['user']


@admin.register(Disponibilita)
class DisponibilitaAdmin(admin.ModelAdmin):
    list_display = ['operatore', 'giorno_settimana', 'ora_inizio', 'ora_fine']
    list_filter = ['giorno_settimana', 'operatore']
    autocomplete_fields = ['operatore']
