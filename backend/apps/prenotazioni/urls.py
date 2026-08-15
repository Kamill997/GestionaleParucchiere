from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import KPIDashboardView, PrenotazioneViewSet, ReportGuadagniView, SlotDisponibiliView

router = DefaultRouter()
router.register('prenotazioni', PrenotazioneViewSet, basename='prenotazioni')

urlpatterns = [
    path('slot-disponibili/', SlotDisponibiliView.as_view(), name='slot-disponibili'),
    path('dashboard/kpi/', KPIDashboardView.as_view(), name='dashboard-kpi'),
    path(
        'dashboard/report-guadagni/',
        ReportGuadagniView.as_view(),
        name='dashboard-report-guadagni',
    ),
    path('', include(router.urls)),
]
