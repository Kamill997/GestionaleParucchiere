"""Import/export in blocco per Clienti (docs/07-import-export-dati.md).

Scope volutamente ridotto rispetto ai docs generici (vedi stato-avanzamento.md,
"Obiettivo attuale"):
- elaborazione SINCRONA (non Celery/async): i volumi realistici di un
  singolo salone sono piccoli, non serve la coda.
- colonne FISSE da template (non un mappatore interattivo di colonne): chi
  importa usa il template scaricabile (vedi genera_template_csv), non
  associa colonne libere a piacere.

Entrambe le semplificazioni sono dichiarate qui, nel README e in
stato-avanzamento.md invece di essere nascoste nel codice.

Tenuto separato da views.py per restare testabile in isolamento, stesso
pattern di apps/prenotazioni/services.py.
"""

import io

import pandas as pd

from .models import Cliente
from .serializers import ClienteSerializer

# Le colonne coincidono esattamente con i campi scrivibili di
# ClienteSerializer (id/user/bloccato/contatore_no_show sono read-only,
# vedi apps/clienti/serializers.py) - vedi stato-avanzamento.md,
# "Decisioni tecniche di questo modulo".
COLONNE = ['nome', 'email', 'telefono', 'note_preferenze']

MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5MB, limite deliberato (stato-avanzamento.md)
ESTENSIONI_CONSENTITE = ('.csv', '.xlsx')


def genera_template_csv() -> str:
    """CSV di esempio scaricabile (docs/07-import-export-dati.md, "Template
    di importazione"): intestazioni corrette + una riga di esempio, per
    ridurre gli errori di mappatura da parte di chi importa."""
    riga_esempio = {
        'nome': 'Mario Rossi',
        'email': 'mario.rossi@example.com',
        'telefono': '3331234567',
        'note_preferenze': 'Es. colore abituale: castano cioccolato',
    }
    buffer = io.StringIO()
    pd.DataFrame([riga_esempio], columns=COLONNE).to_csv(buffer, index=False)
    return buffer.getvalue()


def _leggi_file(file_obj, nome_file: str) -> pd.DataFrame:
    """dtype=str ovunque: senza, pandas convertirebbe es. un telefono
    numerico in float (perdendo eventuali zeri iniziali) - non e' un dato
    su cui inferire un tipo, resta testo dall'origine alla destinazione."""
    if nome_file.lower().endswith('.xlsx'):
        return pd.read_excel(file_obj, dtype=str)
    return pd.read_csv(file_obj, dtype=str)


def importa_clienti(file_obj, nome_file: str, *, request) -> dict:
    """Valida ed elabora un file CSV/Excel di Clienti, riga per riga,
    riusando ClienteSerializer (docs/07-import-export-dati.md, "Validazione":
    "ogni riga viene validata riusando lo stesso serializer DRF usato per
    la creazione manuale", cosi' le regole restano uniche e coerenti tra
    inserimento singolo e massivo).

    Deduplica per email (stato-avanzamento.md): se l'email esiste gia' nel
    DB aggiorna il record esistente, altrimenti ne crea uno nuovo. Mai
    silenzioso: ogni riga finisce nel report come "creata" o "aggiornata".
    Una riga malformata non blocca le altre (continua il ciclo).
    """
    df = _leggi_file(file_obj, nome_file).fillna('')

    colonne_mancanti = [c for c in COLONNE if c not in df.columns]
    if colonne_mancanti:
        return {
            'creati': 0,
            'aggiornati': 0,
            'errori': [
                {
                    'riga': 0,
                    'messaggio': (
                        f'Colonne mancanti: {", ".join(colonne_mancanti)}. '
                        'Usa il template scaricabile invece di modificare le intestazioni.'
                    ),
                }
            ],
            'duplicati_interni': [],
        }

    creati = 0
    aggiornati = 0
    errori = []
    duplicati_interni = []
    email_gia_viste = set()

    for indice, riga in df.iterrows():
        numero_riga = indice + 2  # +1 header, +1 perche' iterrows parte da 0

        dati_riga = {colonna: str(riga.get(colonna, '')).strip() for colonna in COLONNE}
        email = dati_riga['email']

        if email:
            if email in email_gia_viste:
                duplicati_interni.append({'riga': numero_riga, 'email': email})
            email_gia_viste.add(email)

        istanza_esistente = Cliente.objects.filter(email=email).first() if email else None

        serializer = ClienteSerializer(
            instance=istanza_esistente,
            data=dati_riga,
            context={'request': request},
        )
        if not serializer.is_valid():
            errori.append({'riga': numero_riga, 'messaggio': str(serializer.errors)})
            continue

        serializer.save()
        if istanza_esistente:
            aggiornati += 1
        else:
            creati += 1

    return {
        'creati': creati,
        'aggiornati': aggiornati,
        'errori': errori,
        'duplicati_interni': duplicati_interni,
    }


def esporta_clienti_csv(queryset) -> str:
    """Esportazione sincrona (docs/07-import-export-dati.md, "Flusso di
    esportazione": "per dataset piccoli, generazione sincrona e download
    immediato" - un singolo salone rientra sempre in questo caso).

    Non passa da ClienteSerializer: l'intera azione e' gia' riservata ad
    Amministratore a livello di view, quindi note_preferenze compare sempre
    nell'export senza dover rifare il controllo "richiedente e' staff".
    """
    righe = [
        {
            'nome': cliente.nome,
            'email': cliente.email,
            'telefono': cliente.telefono,
            'note_preferenze': cliente.note_preferenze,
        }
        for cliente in queryset
    ]
    buffer = io.StringIO()
    pd.DataFrame(righe, columns=COLONNE).to_csv(buffer, index=False)
    return buffer.getvalue()
