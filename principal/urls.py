"""
urls.py — Roteamento da API — Sistema de Gestão Odontológica
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    UsuarioViewSet,
    PacienteViewSet,
    DentistaViewSet,
    ConsultaViewSet,
    ProntuarioViewSet,
    ProcedimentoViewSet,
    ProntuarioProcedimentoViewSet,
    FinanceiroViewSet,
    EstoqueViewSet,
    DashboardView,
)

router = DefaultRouter()
router.register(r'usuarios',                UsuarioViewSet,                basename='usuario')
router.register(r'pacientes',               PacienteViewSet,               basename='paciente')
router.register(r'dentistas',               DentistaViewSet,               basename='dentista')
router.register(r'consultas',               ConsultaViewSet,               basename='consulta')
router.register(r'prontuarios',             ProntuarioViewSet,             basename='prontuario')
router.register(r'procedimentos',           ProcedimentoViewSet,           basename='procedimento')
router.register(r'prontuario-procedimentos', ProntuarioProcedimentoViewSet, basename='prontuario-procedimento')
router.register(r'financeiro',              FinanceiroViewSet,             basename='financeiro')
router.register(r'estoque',                 EstoqueViewSet,                basename='estoque')

urlpatterns = [
    path('api/v1/', include(router.urls)),
    path('api/v1/dashboard/', DashboardView.as_view(), name='dashboard'),
]

# ─────────────────────────────────────────────────────────────────
# Tabela de endpoints gerados
# ─────────────────────────────────────────────────────────────────
#
#  CRUD automático (para cada recurso):
#  GET    /api/v1/{recurso}/           → list
#  POST   /api/v1/{recurso}/           → create
#  GET    /api/v1/{recurso}/{id}/      → retrieve
#  PUT    /api/v1/{recurso}/{id}/      → update
#  PATCH  /api/v1/{recurso}/{id}/      → partial_update
#  DELETE /api/v1/{recurso}/{id}/      → destroy
#
#  Endpoints extras:
#  GET    /api/v1/dashboard/                        → métricas gerais
#  GET    /api/v1/usuarios/me/                      → usuário logado
#  GET    /api/v1/pacientes/buscar/?q=<termo>       → busca rápida
#  GET    /api/v1/pacientes/{id}/consultas/         → consultas do paciente
#  GET    /api/v1/pacientes/{id}/prontuarios/       → prontuários do paciente
#  GET    /api/v1/pacientes/{id}/financeiro/        → lançamentos do paciente
#  GET    /api/v1/dentistas/{id}/agenda/?data=YYYY-MM-DD → agenda do dentista
#  GET    /api/v1/consultas/hoje/                   → consultas de hoje
#  PATCH  /api/v1/consultas/{id}/confirmar/         → confirmar consulta
#  PATCH  /api/v1/consultas/{id}/cancelar/          → cancelar consulta
#  PATCH  /api/v1/consultas/{id}/realizar/          → marcar como realizada
#  PATCH  /api/v1/consultas/{id}/reagendar/         → reagendar consulta cancelada/falta [NOVO]
#  GET    /api/v1/financeiro/resumo/                → resumo financeiro
#  GET    /api/v1/estoque/alertas/                  → alertas de estoque
#  PATCH  /api/v1/estoque/{id}/ajustar-quantidade/  → ajustar quantidade (adicionar/remover/definir) [NOVO]
#
#  Autenticação JWT:
#  POST   /api/token/                  → obter tokens
#  POST   /api/token/refresh/          → renovar access token
#  POST   /api/token/verify/           → verificar token
#  POST   /api/token/blacklist/        → revogar token (logout)
#
#  Documentação:
#  GET    /api/docs/                   → Swagger UI
#  GET    /api/redoc/                  → ReDoc
#  GET    /api/schema/                 → OpenAPI JSON/YAML