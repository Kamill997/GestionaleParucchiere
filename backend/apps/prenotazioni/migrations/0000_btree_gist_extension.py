from django.contrib.postgres.operations import BtreeGistExtension
from django.db import migrations


class Migration(migrations.Migration):
    """btree_gist e' richiesta perche' l'indice GiST dietro l'ExclusionConstraint
    di Prenotazione combina un confronto di uguaglianza (operatore) con un
    operatore di range/overlap (vedi apps/prenotazioni/models.py). Senza
    questa estensione, la migrazione successiva fallisce a livello di database.
    """

    initial = True

    dependencies = []

    operations = [
        BtreeGistExtension(),
    ]
