from django.db import migrations

RUOLI = ['Cliente', 'Operatore', 'Amministratore']


def crea_ruoli(apps, schema_editor):
    Role = apps.get_model('roles', 'Role')
    for nome in RUOLI:
        Role.objects.get_or_create(nome=nome)


def rimuovi_ruoli(apps, schema_editor):
    Role = apps.get_model('roles', 'Role')
    Role.objects.filter(nome__in=RUOLI).delete()


class Migration(migrations.Migration):
    """Semina i tre ruoli descritti in docs/esempio-settore-parrucchiere.md
    ("Ruoli utente"). Un quarto ruolo (es. Receptionist) puo' essere
    aggiunto in seguito senza toccare l'architettura RBAC sottostante."""

    dependencies = [
        ('roles', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(crea_ruoli, reverse_code=rimuovi_ruoli),
    ]
