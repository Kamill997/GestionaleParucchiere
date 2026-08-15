from datetime import timedelta

from rest_framework import serializers

from .models import Prenotazione, StatoPrenotazione, StatoPresenza
from .services import puo_cancellare_liberamente, slot_e_disponibile

STAFF_ROLES = ('Amministratore', 'Operatore')


def _e_staff(user) -> bool:
    return bool(user) and (user.is_superuser or user.roles.filter(nome__in=STAFF_ROLES).exists())


class PrenotazioneSerializer(serializers.ModelSerializer):
    # Sola lettura, per evitare che ogni lista lato frontend debba fare
    # lookup separati solo per mostrare un nome invece di un id.
    cliente_nome = serializers.CharField(source='cliente.nome', read_only=True)
    operatore_nome = serializers.CharField(source='operatore.nome', read_only=True)
    servizio_nome = serializers.CharField(source='servizio.nome', read_only=True)

    class Meta:
        model = Prenotazione
        fields = [
            'id',
            'cliente',
            'cliente_nome',
            'operatore',
            'operatore_nome',
            'servizio',
            'servizio_nome',
            'inizio',
            'fine',
            'stato',
            'stato_pagamento',
            'importo',
            'stato_presenza',
            'note',
            'creato_il',
        ]
        read_only_fields = ['fine', 'stato', 'stato_presenza', 'creato_il']
        extra_kwargs = {
            # Un Cliente non lo specifica (auto-assegnato al proprio profilo,
            # vedi views.PrenotazioneViewSet.perform_create); solo lo staff
            # deve indicarlo esplicitamente, controllo fatto li' e non qui
            # perche' il serializer non conosce il ruolo di chi chiama.
            'cliente': {'required': False},
            # Di norma calcolato dal prezzo del servizio (vedi validate());
            # resta scrivibile per sconti/eccezioni, ma solo dallo staff.
            'importo': {'required': False},
        }

    def validate(self, attrs):
        operatore = attrs.get('operatore') or getattr(self.instance, 'operatore', None)
        servizio = attrs.get('servizio') or getattr(self.instance, 'servizio', None)
        inizio = attrs.get('inizio') or getattr(self.instance, 'inizio', None)
        richiedente = self.context['request'].user if 'request' in self.context else None

        # stato_pagamento/importo sono dati amministrativi (docs/08-pagamenti.md):
        # un Cliente non deve poter segnarsi da solo come "pagato" o
        # scontarsi il prezzo.
        if ('stato_pagamento' in attrs or 'importo' in attrs) and not _e_staff(richiedente):
            raise serializers.ValidationError("Solo lo staff puo' modificare pagamento/importo.")

        # I controlli attivo/slot/blocco si applicano solo quando si crea una
        # prenotazione nuova, o quando cambiano davvero operatore/servizio/
        # orario: altrimenti modificare solo la nota di una prenotazione gia'
        # confermata fallirebbe se nel frattempo l'operatore o il servizio
        # collegato viene disattivato (trovato in fase di revisione).
        sta_cambiando_pianificazione = (
            self.instance is None
            or 'operatore' in attrs
            or 'servizio' in attrs
            or 'inizio' in attrs
        )

        if sta_cambiando_pianificazione:
            if not operatore.attivo:
                raise serializers.ValidationError({'operatore': 'Operatore non attivo.'})
            if not servizio.attivo:
                raise serializers.ValidationError({'servizio': "Servizio non piu' disponibile."})

            if self.instance is None:
                cliente = attrs.get('cliente') or (
                    richiedente.cliente if richiedente and hasattr(richiedente, 'cliente') else None
                )
                if cliente is not None and cliente.bloccato:
                    raise serializers.ValidationError(
                        'Questo cliente ha prenotazioni bloccate: contatta il salone.'
                    )

            # Durante un reschedule, la prenotazione stessa (ancora nel DB con
            # il vecchio orario finche' non si salva) va esclusa dal controllo,
            # altrimenti puo' risultare in conflitto con se stessa (trovato in
            # fase di revisione).
            escludi_id = self.instance.id if self.instance else None
            if not slot_e_disponibile(
                operatore, servizio, inizio, escludi_prenotazione_id=escludi_id
            ):
                raise serializers.ValidationError(
                    {'inizio': "Slot non disponibile per l'operatore scelto."}
                )
            attrs['fine'] = inizio + timedelta(minutes=servizio.durata_minuti)
            if self.instance is None and 'importo' not in attrs:
                attrs['importo'] = servizio.prezzo

        return attrs


class CancellazioneSerializer(serializers.Serializer):
    """Serializer 'vuoto', usato solo per validare la policy sull'azione
    cancella (vedi views.PrenotazioneViewSet.cancella)."""

    def validate(self, attrs):
        prenotazione = self.context['prenotazione']
        richiedente_e_staff = self.context['richiedente_e_staff']
        if prenotazione.stato != StatoPrenotazione.CONFERMATA:
            raise serializers.ValidationError(
                "Solo una prenotazione confermata puo' essere cancellata."
            )
        if not richiedente_e_staff and not puo_cancellare_liberamente(prenotazione):
            raise serializers.ValidationError(
                'Fuori dai termini di preavviso per la cancellazione: contatta il salone.'
            )
        return attrs


class SegnaPresenzaSerializer(serializers.Serializer):
    """docs/08-pagamenti.md, "Tracciamento presenza": solo staff (verificato
    nella view, non qui - vedi views.PrenotazioneViewSet.segna_presenza)."""

    stato_presenza = serializers.ChoiceField(
        choices=[StatoPresenza.PRESENTE, StatoPresenza.NON_PRESENTE]
    )

    def validate(self, attrs):
        prenotazione = self.context['prenotazione']
        if prenotazione.stato == StatoPrenotazione.CANCELLATA:
            raise serializers.ValidationError(
                'Una prenotazione cancellata non ha una presenza da segnare.'
            )
        return attrs


class SlotDisponibileSerializer(serializers.Serializer):
    inizio = serializers.DateTimeField()
    fine = serializers.DateTimeField()


class ServizioTopSerializer(serializers.Serializer):
    nome = serializers.CharField()
    conteggio = serializers.IntegerField()


class KPIDashboardSerializer(serializers.Serializer):
    prenotazioni_oggi = serializers.IntegerField()
    prenotazioni_settimana = serializers.IntegerField()
    servizio_piu_richiesto = ServizioTopSerializer(allow_null=True)
    tasso_occupazione_oggi = serializers.FloatField()
    fatturato_settimana = serializers.CharField()
    tasso_no_show = serializers.FloatField()


class GuadagnoRigaSerializer(serializers.Serializer):
    """Una riga di guadagno aggregato (per servizio, operatore o cliente -
    vedi services.calcola_report_guadagni)."""

    nome = serializers.CharField()
    totale = serializers.CharField()


class ClienteVicinoBloccoSerializer(serializers.Serializer):
    nome = serializers.CharField()
    contatore_no_show = serializers.IntegerField()
    soglia = serializers.IntegerField()


class ReportGuadagniSerializer(serializers.Serializer):
    """docs/08-pagamenti.md, "Dashboard guadagni (lato Amministratore)"."""

    per_servizio = GuadagnoRigaSerializer(many=True)
    per_operatore = GuadagnoRigaSerializer(many=True)
    top_clienti = GuadagnoRigaSerializer(many=True)
    clienti_vicini_al_blocco = ClienteVicinoBloccoSerializer(many=True)
