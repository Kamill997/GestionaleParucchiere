from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AndamentoProfittiView,
    KPIDashboardView,
    PrenotazioneViewSet,
    ReportGuadagniView,
    RichiestaListaAttesaViewSet,
    SlotDisponibiliView,
)

router = DefaultRouter()
router.register('prenotazioni', PrenotazioneViewSet, basename='prenotazioni')
router.register('lista-attesa', RichiestaListaAttesaViewSet, basename='lista-attesa')

urlpatterns = [
    path('slot-disponibili/', SlotDisponibiliView.as_view(), name='slot-disponibili'),
    path('dashboard/kpi/', KPIDashboardView.as_view(), name='dashboard-kpi'),
    path(
        'dashboard/report-guadagni/',
        ReportGuadagniView.as_view(),
        name='dashboard-report-guadagni',
    ),
    path(
        'dashboard/andamento-profitti/',
        AndamentoProfittiView.as_view(),
        name='dashboard-andamento-profitti',
    ),
    path('', include(router.urls)),
]
