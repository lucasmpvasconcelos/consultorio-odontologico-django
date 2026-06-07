"""
views.py — Módulo Pacientes
Django REST Framework
"""
 
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
 
from .models import Paciente
from .serializers import (
    PacienteListSerializer,
    PacienteDetailSerializer,
    ConsultaResumoSerializer,
    ProntuarioResumoSerializer,
)
from .filters_urls import PacienteFilter
 
 
class PacienteViewSet(viewsets.ModelViewSet):
    """
    ViewSet completo para Pacientes.
 
    Endpoints gerados automaticamente:
      GET    /pacientes/           → list()
      POST   /pacientes/           → create()
      GET    /pacientes/{id}/      → retrieve()
      PUT    /pacientes/{id}/      → update()
      PATCH  /pacientes/{id}/      → partial_update()
      DELETE /pacientes/{id}/      → destroy()
 
    Endpoints extras:
      GET    /pacientes/{id}/consultas/   → consultas do paciente
      GET    /pacientes/{id}/prontuarios/ → prontuários do paciente
      GET    /pacientes/buscar/           → busca por nome/CPF/telefone
    """
 
    queryset = Paciente.objects.all().order_by('nome_completo')
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = PacienteFilter
    search_fields = ['nome_completo', 'cpf', 'email', 'telefone']
    ordering_fields = ['nome_completo', 'criado_em', 'data_nascimento']
    ordering = ['nome_completo']
 
    def get_serializer_class(self):
        if self.action == 'list':
            return PacienteListSerializer
        return PacienteDetailSerializer
 
    # ── Actions extras ──────────────────────────────────────────
 
    @action(detail=True, methods=['get'], url_path='consultas')
    def consultas(self, request, pk=None):
        """Retorna todas as consultas do paciente."""
        paciente = self.get_object()
        qs = paciente.consultas.select_related('dentista').order_by('-data_hora')
        serializer = ConsultaResumoSerializer(qs, many=True)
        return Response(serializer.data)
 
    @action(detail=True, methods=['get'], url_path='prontuarios')
    def prontuarios(self, request, pk=None):
        """Retorna todos os prontuários do paciente."""
        paciente = self.get_object()
        qs = paciente.prontuarios.select_related('dentista').order_by('-data_atendimento')
        serializer = ProntuarioResumoSerializer(qs, many=True)
        return Response(serializer.data)
 
    @action(detail=False, methods=['get'], url_path='buscar')
    def buscar(self, request):
        """
        Busca rápida por nome, CPF ou telefone.
        Query param: ?q=<termo>
        """
        termo = request.query_params.get('q', '').strip()
        if not termo:
            return Response(
                {'detail': 'Informe o parâmetro ?q= para busca.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        qs = Paciente.objects.filter(
            Q(nome_completo__icontains=termo) |
            Q(cpf__icontains=termo)           |
            Q(telefone__icontains=termo)      |
            Q(email__icontains=termo)
        ).order_by('nome_completo')[:20]
        serializer = PacienteListSerializer(qs, many=True)
        return Response(serializer.data)
 
    def destroy(self, request, *args, **kwargs):
        """Impede exclusão de paciente com consultas vinculadas."""
        paciente = self.get_object()
        if paciente.consultas.exists():
            return Response(
                {'detail': 'Não é possível excluir um paciente com consultas registradas.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().destroy(request, *args, **kwargs)