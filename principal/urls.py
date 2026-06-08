from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UsuarioViewSet, PacienteViewSet, DentistaViewSet,
    ConsultaViewSet, ProntuarioViewSet, ProcedimentoViewSet,
    ProntuarioProcedimentoViewSet, FinanceiroViewSet, EstoqueViewSet,
)

router = DefaultRouter()

router.register(r'usuarios', UsuarioViewSet, basename='usuario')
router.register(r'pacientes', PacienteViewSet, basename='paciente')
router.register(r'dentistas', DentistaViewSet, basename='dentista')
router.register(r'consultas', ConsultaViewSet, basename='consulta')
router.register(r'prontuarios', ProntuarioViewSet, basename='prontuario')
router.register(r'procedimentos', ProcedimentoViewSet, basename='procedimento')
router.register(r'prontuario-procedimentos', ProntuarioProcedimentoViewSet, basename='prontuario-procedimento')
router.register(r'financeiro', FinanceiroViewSet, basename='financeiro')
router.register(r'estoque', EstoqueViewSet, basename='estoque')

urlpatterns = [
    path('api/v1/', include(router.urls)),
]