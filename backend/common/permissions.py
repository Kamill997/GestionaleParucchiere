"""Permessi DRF custom condivisi tra le app.

Fase 2: guard RBAC basato sui ruoli custom (apps.roles.Role), non sui
Group/Permission nativi di Django (vedi docs/02-backend.md, "Autorizzazione").
"""

from rest_framework.permissions import SAFE_METHODS, BasePermission


class HasRole(BasePermission):
    """Autorizza se l'utente ha almeno uno dei ruoli in `required_roles`.

    Un superuser passa sempre (comodo per amministrazione/debug), coerente
    con il comportamento standard di Django is_superuser.
    """

    required_roles: tuple[str, ...] = ()

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        return user.roles.filter(nome__in=self.required_roles).exists()


def roles_required(*roles: str) -> type[HasRole]:
    """Genera una classe di permesso DRF che richiede uno dei ruoli indicati.

    Uso: permission_classes = [roles_required('Amministratore')]
    """
    return type('RoleRequired', (HasRole,), {'required_roles': roles})


class ReadOnlyOrRoleRequired(BasePermission):
    """GET/HEAD/OPTIONS: chiunque sia autenticato. Altri metodi (scrittura):
    solo i ruoli in `required_roles`. Utile per cataloghi (Servizi,
    Operatori) che tutti possono sfogliare ma solo lo staff puo' modificare.
    """

    required_roles: tuple[str, ...] = ()

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if request.method in SAFE_METHODS:
            return True
        if user.is_superuser:
            return True
        return user.roles.filter(nome__in=self.required_roles).exists()


def read_only_or_roles_required(*roles: str) -> type[ReadOnlyOrRoleRequired]:
    """Uso: permission_classes = [read_only_or_roles_required('Amministratore')]"""
    return type('ReadOnlyOrRoleRequired', (ReadOnlyOrRoleRequired,), {'required_roles': roles})
