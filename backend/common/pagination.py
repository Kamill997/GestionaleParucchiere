from rest_framework.pagination import PageNumberPagination


class StandardResultsSetPagination(PageNumberPagination):
    """Paginazione di default per i viewset DRF del progetto.

    Impostata come DEFAULT_PAGINATION_CLASS in config/settings.py,
    cosi' ogni viewset la eredita senza doverla dichiarare esplicitamente.
    """

    page_size = 25
    page_size_query_param = 'page_size'
    max_page_size = 100
