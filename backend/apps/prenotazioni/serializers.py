from datetime import timedelta

from django.utils import timezone
from rest_framework import serializers

from apps.servizi.models import Servizio

from .models import Prenotazione, RichiestaListaAttesa, StatoListaAttesa, StatoPrenotazione, StatoPresenza
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
    servizi_aggiuntivi = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Servizio.objects.filter(attivo=True),
        required=False,
    )
    servizi_aggiuntivi_dettaglio = serializers.SerializerMethodField(read_only=True)
    durata_totale_minuti = serializers.SerializerMethodField(read_only=True)

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
            'servizi_aggiuntivi',
            'servizi_aggiuntivi_dettaglio',
            'durata_totale_minuti',
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

    def get_servizi_aggiuntivi_dettaglio(self, obj):
        return [
            {
                'id': str(s.id),
                'nome': s.nome,
                'prezzo': str(s.prezzo),
                'durata_minuti': s.durata_minuti,
            }
            for s in obj.servizi_aggiuntivi.all()
        ]

    def get_durata_totale_minuti(self, obj):
        tot = obj.servizio.durata_minuti if obj.servizio else 0
        tot += sum(s.durata_minuti for s in obj.servizi_aggiuntivi.all())
        return tot

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

        servizi_aggiuntivi = attrs.get('servizi_aggiuntivi')
        if servizi_aggiuntivi is None and self.instance:
            servizi_aggiuntivi = list(self.instance.servizi_aggiuntivi.all())
        elif servizi_aggiuntivi is None:
            servizi_aggiuntivi = []

        durata_totale = (servizio.durata_minuti if servizio else 0) + sum(
            s.durata_minuti for s in servizi_aggiuntivi
        )
        prezzo_totale = (servizio.prezzo if servizio else 0) + sum(
            s.prezzo for s in servizi_aggiuntivi
        )

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
            or 'servizi_aggiuntivi' in attrs
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
            if (
                self.instance is None
                and not _e_staff(richiedente)
                and inizio <= timezone.now()
            ):
                raise serializers.ValidationError(
                    {'inizio': "Non è possibile prenotare un appuntamento per un orario già trascorso."}
                )
            if not slot_e_disponibile(
                operatore,
                servizio,
                inizio,
                escludi_prenotazione_id=escludi_id,
                durata_totale_minuti=durata_totale,
            ):
                raise serializers.ValidationError(
                    {'inizio': "Slot non disponibile per l'operatore scelto."}
                )
            attrs['fine'] = inizio + timedelta(minutes=durata_totale)
            if self.instance is None and 'importo' not in attrs:
                attrs['importo'] = prezzo_totale

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


class RichiestaListaAttesaSerializer(serializers.ModelSerializer):
    cliente_nome = serializers.CharField(source='cliente.nome', read_only=True)
    servizio_nome = serializers.CharField(source='servizio.nome', read_only=True)
    operatore_nome = serializers.CharField(source='operatore.nome', read_only=True, allow_null=True)

    class Meta:
        model = RichiestaListaAttesa
        fields = [
            'id',
            'cliente',
            'cliente_nome',
            'servizio',
            'servizio_nome',
            'operatore',
            'operatore_nome',
            'data',
            'ora_preferita',
            'stato',
            'note',
            'notificato_il',
            'creato_il',
        ]
        read_only_fields = ['stato', 'notificato_il', 'creato_il']
        extra_kwargs = {
            'cliente': {'required': False},
        }

    def validate_data(self, value):
        if value < timezone.localdate():
            raise serializers.ValidationError("Non puoi inserirti in lista d'attesa per una data passata.")
        return value

    def validate(self, attrs):
        cliente = attrs.get('cliente')
        request = self.context.get('request')
        target_cliente = cliente
        if not target_cliente and request and hasattr(request.user, 'cliente'):
            target_cliente = request.user.cliente

        servizio = attrs.get('servizio') or getattr(self.instance, 'servizio', None)
        data = attrs.get('data') or getattr(self.instance, 'data', None)

        if target_cliente and servizio and data:
            qs = RichiestaListaAttesa.objects.filter(
                cliente=target_cliente,
                servizio=servizio,
                data=data,
                stato__in=[StatoListaAttesa.IN_ATTESA, StatoListaAttesa.NOTIFICATO],
            )
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError(
                    "Hai già una richiesta attiva in lista d'attesa per questo servizio in questa data."
                )

        return attrs


class SlotDisponibileSerializer(serializers.Serializer):
    inizio = serializers.DateTimeField()
    fine = serializers.DateTimeField()
    disponibile = serializers.BooleanField(default=True)


class ServizioTopSerializer(serializers.Serializer):
    nome = serializers.CharField()
    conteggio = serializers.IntegerField()


class KPIDashboardSerializer(serializers.Serializer):
    prenotazioni_oggi = serializers.IntegerField()
    prenotazioni_settimana = serializers.IntegerField()
    servizio_piu_richiesto = ServizioTopSerializer(allow_null=True)
    tasso_occupazione_oggi = serializers.FloatField()
    fatturato_settimana = serializers.CharField(allow_null=True, required=False)
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


class AndamentoGiornoSerializer(serializers.Serializer):
    data = serializers.CharField()
    etichetta = serializers.CharField()
    totale = serializers.FloatField()
    appuntamenti = serializers.IntegerField()


class CategoriaFatturatoSerializer(serializers.Serializer):
    categoria = serializers.CharField()
    totale = serializers.FloatField()
    appuntamenti = serializers.IntegerField()
    percentuale = serializers.FloatField()


class OperatoreFatturatoSerializer(serializers.Serializer):
    operatore = serializers.CharField()
    totale = serializers.FloatField()
    appuntamenti = serializers.IntegerField()


class AndamentoProfittiSerializer(serializers.Serializer):
    totale_periodo = serializers.FloatField()
    media_giornaliera = serializers.FloatField()
    giorni = AndamentoGiornoSerializer(many=True)
    categorie = CategoriaFatturatoSerializer(many=True)
    operatori = OperatoreFatturatoSerializer(many=True)
