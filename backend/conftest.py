"""Fixture pytest condivise tra le app (login autenticato con CSRF, utenti
con ruoli). Un conftest.py a livello di progetto le rende disponibili a
tutti i test senza doverle reimportare ovunque."""

import pytest
from rest_framework.test import APIClient

from apps.clienti.models import Cliente
from apps.roles.models import Role
from apps.users.models import User

DEFAULT_PASSWORD = 'una-password-robusta-123'


@pytest.fixture
def api_client():
    return APIClient(enforce_csrf_checks=True)


def login_with_csrf(client: APIClient, email: str, password: str = DEFAULT_PASSWORD) -> str:
    """Effettua login e restituisce il token CSRF da usare nelle richieste
    mutanti successive (vedi backend/common/authentication.py)."""
    client.get('/api/v1/auth/csrf/')
    csrf_token = client.cookies['csrftoken'].value
    client.post(
        '/api/v1/auth/login/', {'email': email, 'password': password}, HTTP_X_CSRFTOKEN=csrf_token
    )
    return csrf_token


def _utente_con_ruolo(api_client, email, ruolo_nome):
    user = User.objects.create_user(email=email, password=DEFAULT_PASSWORD)
    ruolo, _ = Role.objects.get_or_create(nome=ruolo_nome)
    user.roles.add(ruolo)
    user.csrf_token = login_with_csrf(api_client, email)
    return user


@pytest.fixture
def cliente_utente(api_client):
    """Utente con ruolo Cliente, gia' con sessione autenticata (cookie+CSRF).

    Crea anche il record Cliente collegato: rispecchia l'invariante reale
    garantito da RegisterView.perform_create (vedi apps/users/views.py),
    dato che qui l'utente e' creato direttamente via ORM, non passando
    dall'endpoint /auth/register/.
    """
    user = _utente_con_ruolo(api_client, 'cliente@example.com', 'Cliente')
    Cliente.objects.create(user=user, nome='Cliente Di Prova', email=user.email)
    return user


@pytest.fixture
def operatore_utente(api_client):
    """Utente con ruolo Operatore, sessione autenticata. NON crea un record
    Operatore collegato: nel modello reale il profilo Operatore va creato
    esplicitamente da un Amministratore tramite l'API (vedi apps/operatori),
    non e' automatico come per Cliente alla registrazione."""
    return _utente_con_ruolo(api_client, 'operatore@example.com', 'Operatore')


@pytest.fixture
def admin_utente(api_client):
    return _utente_con_ruolo(api_client, 'admin@example.com', 'Amministratore')
