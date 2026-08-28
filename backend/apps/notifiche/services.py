"""Creazione notifiche in-app + invio email collegato
(docs/03-componenti-e-workflow.md "Notifiche",
docs/esempio-settore-parrucchiere.md "Notifiche specifiche del settore",
docs/08-pagamenti.md "Notifiche collegate").

Tenuto separato da models.py/views.py per restare facilmente chiamabile
dagli altri moduli (prenotazioni, clienti) senza creare dipendenze
circolari a livello di import di modulo - le app che generano eventi
importano da qui dentro le proprie funzioni, non in testa al file.
"""

from django.conf import settings
from django.core.mail import send_mail

from .models import Notifica, TipoNotifica

# Tipi che generano anche un'email, secondo le tabelle nei docs. Gli altri
# restano solo in-app: "nuova prenotazione ricevuta" e' "in-app,
# eventualmente push" (non email); "cliente bloccato/sbloccato" e'
# "notifica interna" per l'Amministratore.
TIPI_CON_EMAIL = {
    TipoNotifica.CONFERMA_PRENOTAZIONE,
    TipoNotifica.CANCELLAZIONE_PRENOTAZIONE,
    TipoNotifica.PROMEMORIA_PRENOTAZIONE,
    TipoNotifica.SOGLIA_NO_SHOW_RAGGIUNTA,
}


def _invia_email(destinatario_email: str, titolo: str, messaggio: str) -> None:
    send_mail(
        subject=titolo,
        message=messaggio,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[destinatario_email],
        fail_silently=True,
    )


def crea_notifica(
    destinatario_user, tipo: str, titolo: str, messaggio: str, *, link=''
) -> Notifica:
    """destinatario_user: un utente CON account (Operatore, Amministratore,
    o Cliente registrato). Per un Cliente ospite (senza account) usare
    notifica_cliente sotto, non questa direttamente - non esiste uno User
    a cui agganciare una riga Notifica."""
    notifica = Notifica.objects.create(
        destinatario=destinatario_user, tipo=tipo, titolo=titolo, messaggio=messaggio, link=link
    )
    if tipo in TIPI_CON_EMAIL and destinatario_user.email:
        _invia_email(destinatario_user.email, titolo, messaggio)

    # Push non-blocking: ignorato silenziosamente se VAPID non e' configurato
    # (sviluppo, CI) o se il task push fallisce per qualsiasi motivo.
    # Non blocca mai la creazione della notifica in-app.
    try:
        from .push_services import invia_push_a_utente

        invia_push_a_utente(destinatario_user, titolo, messaggio, link=link)
    except Exception:
        pass

    return notifica


def notifica_cliente(
    cliente, tipo: str, titolo: str, messaggio: str, *, link=''
) -> Notifica | None:
    """Un Cliente puo' non avere un account (prenotazione da ospite, vedi
    docs/08-pagamenti.md): se c'e' uno User collegato, notifica in-app +
    email come chiunque altro; altrimenti solo email diretta all'indirizzo
    del Cliente stesso (niente in-app senza un account a cui agganciarla)."""
    if cliente.user:
        return crea_notifica(cliente.user, tipo, titolo, messaggio, link=link)
    if tipo in TIPI_CON_EMAIL and cliente.email:
        _invia_email(cliente.email, titolo, messaggio)
    return None


def notifica_amministratori(tipo: str, titolo: str, messaggio: str, *, link='') -> list[Notifica]:
    """docs/08-pagamenti.md: "Cliente bloccato/sbloccato -> Amministratore
    (notifica interna, utile a tenere traccia delle decisioni prese)" - va
    a TUTTI gli Amministratori, non a uno solo."""
    from apps.users.models import User

    amministratori = User.objects.filter(roles__nome='Amministratore').distinct()
    return [crea_notifica(admin, tipo, titolo, messaggio, link=link) for admin in amministratori]
