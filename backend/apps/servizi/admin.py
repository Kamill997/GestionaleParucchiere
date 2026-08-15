from django.contrib import admin

from .models import Servizio


@admin.register(Servizio)
class ServizioAdmin(admin.ModelAdmin):
    list_display = ['nome', 'categoria', 'durata_minuti', 'prezzo', 'attivo']
    list_filter = ['categoria', 'attivo']
    search_fields = ['nome', 'descrizione']
