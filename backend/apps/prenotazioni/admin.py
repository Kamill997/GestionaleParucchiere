from django.contrib import admin

from .models import Prenotazione


@admin.register(Prenotazione)
class PrenotazioneAdmin(admin.ModelAdmin):
    list_display = [
        'inizio',
        'cliente',
        'operatore',
        'servizio',
        'stato',
        'stato_pagamento',
        'stato_presenza',
    ]
    list_filter = ['stato', 'stato_pagamento', 'stato_presenza', 'operatore']
    search_fields = ['cliente__nome', 'cliente__email', 'operatore__nome']
    autocomplete_fields = ['cliente', 'operatore', 'servizio']
    date_hierarchy = 'inizio'
