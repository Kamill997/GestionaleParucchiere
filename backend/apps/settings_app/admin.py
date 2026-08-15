from django.contrib import admin

from .models import Impostazione


@admin.register(Impostazione)
class ImpostazioneAdmin(admin.ModelAdmin):
    list_display = ['chiave', 'valore', 'descrizione']
    search_fields = ['chiave']
