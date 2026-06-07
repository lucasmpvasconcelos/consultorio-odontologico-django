"""
filters.py — Filtros do módulo Pacientes
"""
 
import django_filters
from .models import Paciente
 
 
class PacienteFilter(django_filters.FilterSet):
    nome      = django_filters.CharFilter(field_name='nome_completo', lookup_expr='icontains')
    cpf       = django_filters.CharFilter(lookup_expr='icontains')
    plano     = django_filters.CharFilter(field_name='plano_odonto', lookup_expr='icontains')
    nascimento_de  = django_filters.DateFilter(field_name='data_nascimento', lookup_expr='gte')
    nascimento_ate = django_filters.DateFilter(field_name='data_nascimento', lookup_expr='lte')
    criado_de      = django_filters.DateTimeFilter(field_name='criado_em', lookup_expr='gte')
 
    class Meta:
        model = Paciente
        fields = ['nome', 'cpf', 'plano', 'nascimento_de', 'nascimento_ate', 'criado_de']
 
 
# ─────────────────────────────────────────────────────────────────
"""
urls.py — Roteamento do módulo Pacientes
"""
 
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PacienteViewSet
 
router = DefaultRouter()
router.register(r'pacientes', PacienteViewSet, basename='paciente')
 
urlpatterns = [
    path('api/v1/', include(router.urls)),
]
 
# ─────────────────────────────────────────────────────────────────
# Tabela de endpoints gerados
# ─────────────────────────────────────────────────────────────────
#
#  Método   Endpoint                              Descrição
#  ───────  ────────────────────────────────────  ─────────────────────────────
#  GET      /api/v1/pacientes/                    Listar pacientes (paginado)
#  POST     /api/v1/pacientes/                    Criar paciente
#  GET      /api/v1/pacientes/{id}/               Detalhar paciente
#  PUT      /api/v1/pacientes/{id}/               Atualizar paciente (completo)
#  PATCH    /api/v1/pacientes/{id}/               Atualizar paciente (parcial)
#  DELETE   /api/v1/pacientes/{id}/               Excluir paciente
#  GET      /api/v1/pacientes/{id}/consultas/     Consultas do paciente
#  GET      /api/v1/pacientes/{id}/prontuarios/   Prontuários do paciente
#  GET      /api/v1/pacientes/buscar/?q=termo     Busca rápida
#
# Filtros disponíveis na listagem:
#   ?nome=joao
#   ?cpf=123
#   ?plano=unimed
#   ?nascimento_de=1990-01-01&nascimento_ate=2000-12-31
#   ?search=<busca global>
#   ?ordering=nome_completo | -criado_em | data_nascimento
#   ?page=2&page_size=20