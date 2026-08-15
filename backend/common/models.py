import uuid

from django.db import models


class UUIDModel(models.Model):
    """Base astratta: id UUID invece del BigAutoField di default.

    Tutti gli schema ER in docs/*.md usano `uuid id PK` per ogni entita';
    questa classe evita di ripetere la dichiarazione in ogni modello.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True
