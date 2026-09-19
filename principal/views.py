"""
views.py — Sistema de Gestão Odontológica
Django REST Framework — ViewSets completos com filtros, busca e ações extras
"""

from datetime import date, timedelta

from django.db.models import Q, Sum, Count
from django.utils import timezone

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend

from .models import (
    Usuario, Paciente, Dentista,
    Consulta, Prontuario, Procedimento,
    ProntuarioProcedimento, Financeiro, Estoque,
)
from .serializers import (
    PacienteListSerializer,
    PacienteDetailSerializer,
    ConsultaResumoSerializer,
    ProntuarioResumoSerializer,
    UsuarioSerializer,
    UsuarioCreateSerializer,
    DentistaSerializer,
    ProcedimentoSerializer,
    FinanceiroSerializer,
    EstoqueSerializer,
    ConsultaSerializer,
    ProntuarioSerializer,
    ProntuarioProcedimentoSerializer,
)
from .filters import (
    PacienteFilter,
    ConsultaFilter,
    FinanceiroFilter,
    EstoqueFilter,
    DentistaFilter,
    ProcedimentoFilter,
    ProntuarioFilter,
)


# ─────────────────────────────────────────
# DASHBOARD
# ─────────────────────────────────────────

class DashboardView(APIView):
    """
    GET /api/v1/dashboard/
    Retorna métricas resumidas para a tela inicial do sistema.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        hoje     = date.today()
        amanha   = hoje + timedelta(days=1)
        inicio_semana = hoje - timedelta(days=hoje.weekday())
        fim_semana    = inicio_semana + timedelta(days=6)
        inicio_mes    = hoje.replace(day=1)

        # ── Consultas ──────────────────────────────────────────────
        consultas_hoje    = Consulta.objects.filter(data_hora__date=hoje)
        consultas_semana  = Consulta.objects.filter(data_hora__date__range=(inicio_semana, fim_semana))
        consultas_mes     = Consulta.objects.filter(data_hora__date__gte=inicio_mes)

        # ── Financeiro do mês ──────────────────────────────────────
        receitas_mes = Financeiro.objects.filter(
            tipo='receita', status='pago',
            pago_em__gte=inicio_mes,
        ).aggregate(total=Sum('valor'))['total'] or 0

        despesas_mes = Financeiro.objects.filter(
            tipo='despesa', status='pago',
            pago_em__gte=inicio_mes,
        ).aggregate(total=Sum('valor'))['total'] or 0

        contas_pendentes = Financeiro.objects.filter(
            status='pendente', vencimento__lt=hoje
        ).count()

        # ── Estoque ────────────────────────────────────────────────
        from django.db.models import F
        estoque_critico = Estoque.objects.filter(quantidade__lte=F('quantidade_minima')).count()
        estoque_vencendo = Estoque.objects.filter(
            validade__isnull=False,
            validade__lte=hoje + timedelta(days=30),
            validade__gte=hoje,
        ).count()

        # ── Totais gerais ──────────────────────────────────────────
        total_pacientes  = Paciente.objects.count()
        total_dentistas  = Dentista.objects.count()
        novos_pacientes_mes = Paciente.objects.filter(criado_em__date__gte=inicio_mes).count()

        return Response({
            'data_referencia': hoje,
            'consultas': {
                'hoje_total':      consultas_hoje.count(),
                'hoje_agendadas':  consultas_hoje.filter(status='agendada').count(),
                'hoje_confirmadas': consultas_hoje.filter(status='confirmada').count(),
                'hoje_realizadas': consultas_hoje.filter(status='realizada').count(),
                'semana_total':    consultas_semana.count(),
                'mes_total':       consultas_mes.count(),
                'mes_canceladas':  consultas_mes.filter(status='cancelada').count(),
                'mes_faltas':      consultas_mes.filter(status='falta').count(),
            },
            'financeiro': {
                'receitas_mes':      float(receitas_mes),
                'despesas_mes':      float(despesas_mes),
                'lucro_mes':         float(receitas_mes - despesas_mes),
                'contas_vencidas':   contas_pendentes,
            },
            'estoque': {
                'itens_criticos':   estoque_critico,
                'itens_vencendo':   estoque_vencendo,
            },
            'pacientes': {
                'total':            total_pacientes,
                'novos_mes':        novos_pacientes_mes,
            },
            'dentistas': {
                'total':            total_dentistas,
            },
        })


# ─────────────────────────────────────────
# USUÁRIO
# ─────────────────────────────────────────

class UsuarioViewSet(viewsets.ModelViewSet):
    """
    ViewSet de Usuários.
    Usa serializer especial com criação segura de senha.
    """
    queryset = Usuario.objects.all().order_by('id')
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields   = ['username', 'first_name', 'last_name', 'email']
    ordering_fields = ['username', 'date_joined', 'perfil']

    def get_serializer_class(self):
        if self.action == 'create':
            return UsuarioCreateSerializer
        return UsuarioSerializer

    @action(detail=False, methods=['get'], url_path='me')
    def me(self, request):
        """Retorna o usuário autenticado atual."""
        serializer = UsuarioSerializer(request.user)
        return Response(serializer.data)


# ─────────────────────────────────────────
# PACIENTE
# ─────────────────────────────────────────

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
      GET    /pacientes/{id}/financeiro/  → lançamentos do paciente
      GET    /pacientes/buscar/           → busca por nome/CPF/telefone
    """

    queryset = Paciente.objects.all().order_by('nome_completo')
    permission_classes  = [IsAuthenticated]
    filter_backends     = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class     = PacienteFilter
    search_fields       = ['nome_completo', 'cpf', 'email', 'telefone']
    ordering_fields     = ['nome_completo', 'criado_em', 'data_nascimento']
    ordering            = ['nome_completo']

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

    @action(detail=True, methods=['get'], url_path='financeiro')
    def financeiro(self, request, pk=None):
        """Retorna o histórico financeiro do paciente."""
        paciente = self.get_object()
        qs = paciente.lancamentos.order_by('-criado_em')
        serializer = FinanceiroSerializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='buscar')
    def buscar(self, request):
        """
        Busca rápida por nome, CPF, telefone ou e-mail.
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


# ─────────────────────────────────────────
# DENTISTA
# ─────────────────────────────────────────

class DentistaViewSet(viewsets.ModelViewSet):
    """ViewSet de Dentistas com filtros e agenda do dia."""
    queryset = Dentista.objects.all().order_by('nome_completo')
    serializer_class    = DentistaSerializer
    permission_classes  = [IsAuthenticated]
    filter_backends     = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class     = DentistaFilter
    search_fields       = ['nome_completo', 'cro', 'especialidade', 'email']
    ordering_fields     = ['nome_completo', 'especialidade']

    @action(detail=True, methods=['get'], url_path='agenda')
    def agenda(self, request, pk=None):
        """Retorna a agenda do dentista para uma data (padrão: hoje)."""
        dentista = self.get_object()
        data_str = request.query_params.get('data')
        try:
            data = date.fromisoformat(data_str) if data_str else date.today()
        except ValueError:
            return Response({'detail': 'Data inválida. Use formato YYYY-MM-DD.'}, status=400)

        consultas = dentista.consultas.filter(
            data_hora__date=data
        ).select_related('paciente').order_by('data_hora')

        serializer = ConsultaSerializer(consultas, many=True)
        return Response({
            'dentista': str(dentista),
            'data':     data,
            'total':    consultas.count(),
            'consultas': serializer.data,
        })


# ─────────────────────────────────────────
# CONSULTA
# ─────────────────────────────────────────

class ConsultaViewSet(viewsets.ModelViewSet):
    """
    ViewSet de Consultas com filtros e ações de confirmação/cancelamento/reagendamento.
    """
    queryset = Consulta.objects.select_related('paciente', 'dentista').order_by('-data_hora')
    serializer_class    = ConsultaSerializer
    permission_classes  = [IsAuthenticated]
    filter_backends     = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class     = ConsultaFilter
    search_fields       = ['paciente__nome_completo', 'paciente__cpf', 'dentista__nome_completo', 'observacoes']
    ordering_fields     = ['data_hora', 'status', 'tipo', 'criado_em']

    @action(detail=True, methods=['patch'], url_path='confirmar')
    def confirmar(self, request, pk=None):
        """Confirma uma consulta agendada."""
        consulta = self.get_object()
        if consulta.status not in ('agendada', 'confirmada'):
            return Response(
                {'detail': f'Não é possível confirmar uma consulta com status "{consulta.get_status_display()}".'},
                status=status.HTTP_400_BAD_REQUEST
            )
        consulta.status    = Consulta.Status.CONFIRMADA
        consulta.confirmada = True
        consulta.save(update_fields=['status', 'confirmada'])
        return Response(ConsultaSerializer(consulta).data)

    @action(detail=True, methods=['patch'], url_path='cancelar')
    def cancelar(self, request, pk=None):
        """Cancela uma consulta."""
        consulta = self.get_object()
        if consulta.status in ('realizada', 'cancelada'):
            return Response(
                {'detail': f'Não é possível cancelar uma consulta com status "{consulta.get_status_display()}".'},
                status=status.HTTP_400_BAD_REQUEST
            )
        consulta.status = Consulta.Status.CANCELADA
        consulta.save(update_fields=['status'])
        return Response(ConsultaSerializer(consulta).data)

    @action(detail=True, methods=['patch'], url_path='realizar')
    def realizar(self, request, pk=None):
        """Marca uma consulta como realizada."""
        consulta = self.get_object()
        if consulta.status not in ('agendada', 'confirmada'):
            return Response(
                {'detail': f'Não é possível realizar uma consulta com status "{consulta.get_status_display()}".'},
                status=status.HTTP_400_BAD_REQUEST
            )
        consulta.status = Consulta.Status.REALIZADA
        consulta.save(update_fields=['status'])
        return Response(ConsultaSerializer(consulta).data)

    @action(detail=True, methods=['patch'], url_path='reagendar')
    def reagendar(self, request, pk=None):
        """
        Reagenda uma consulta cancelada ou com falta, definindo nova data/hora.
        Body: { "data_hora": "YYYY-MM-DDTHH:MM:SS", "duracao_min": 60 (opcional) }
        """
        consulta = self.get_object()
        if consulta.status not in ('cancelada', 'falta'):
            return Response(
                {'detail': f'Só é possível reagendar consultas canceladas ou com falta. '
                           f'Status atual: "{consulta.get_status_display()}".'},
                status=status.HTTP_400_BAD_REQUEST
            )
        nova_data = request.data.get('data_hora')
        if not nova_data:
            return Response(
                {'detail': 'Informe o campo "data_hora" com a nova data/hora.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        serializer = ConsultaSerializer(consulta, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        consulta = serializer.save(status=Consulta.Status.AGENDADA, confirmada=False)
        return Response(ConsultaSerializer(consulta).data)

    @action(detail=False, methods=['get'], url_path='hoje')
    def hoje(self, request):
        """Retorna todas as consultas de hoje."""
        qs = self.get_queryset().filter(data_hora__date=date.today())
        serializer = ConsultaSerializer(qs, many=True)
        return Response({'data': date.today(), 'total': qs.count(), 'consultas': serializer.data})


# ─────────────────────────────────────────
# PRONTUÁRIO
# ─────────────────────────────────────────

class ProntuarioViewSet(viewsets.ModelViewSet):
    """ViewSet de Prontuários."""
    queryset = Prontuario.objects.select_related('paciente', 'dentista').order_by('-data_atendimento')
    serializer_class   = ProntuarioSerializer
    permission_classes = [IsAuthenticated]
    filter_backends    = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class    = ProntuarioFilter
    search_fields      = ['paciente__nome_completo', 'paciente__cpf', 'diagnostico', 'anamnese']
    ordering_fields    = ['data_atendimento', 'criado_em']


# ─────────────────────────────────────────
# PROCEDIMENTO
# ─────────────────────────────────────────

class ProcedimentoViewSet(viewsets.ModelViewSet):
    """ViewSet de Procedimentos (catálogo)."""
    queryset = Procedimento.objects.all().order_by('categoria', 'nome')
    serializer_class   = ProcedimentoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends    = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class    = ProcedimentoFilter
    search_fields      = ['nome', 'descricao', 'codigo_tuss']
    ordering_fields    = ['nome', 'categoria', 'valor_padrao', 'duracao_media']


# ─────────────────────────────────────────
# PRONTUÁRIO ↔ PROCEDIMENTO
# ─────────────────────────────────────────

class ProntuarioProcedimentoViewSet(viewsets.ModelViewSet):
    """ViewSet de Procedimentos vinculados a Prontuários."""
    queryset = ProntuarioProcedimento.objects.select_related('prontuario', 'procedimento').order_by('id')
    serializer_class   = ProntuarioProcedimentoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends    = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields   = ['prontuario', 'procedimento', 'dente']


# ─────────────────────────────────────────
# FINANCEIRO
# ─────────────────────────────────────────

class FinanceiroViewSet(viewsets.ModelViewSet):
    """ViewSet de Lançamentos Financeiros com filtros e resumo."""
    queryset = Financeiro.objects.select_related('paciente', 'consulta').order_by('-criado_em')
    serializer_class   = FinanceiroSerializer
    permission_classes = [IsAuthenticated]
    filter_backends    = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class    = FinanceiroFilter
    search_fields      = ['descricao', 'paciente__nome_completo', 'observacoes']
    ordering_fields    = ['valor', 'vencimento', 'pago_em', 'criado_em', 'status']

    @action(detail=False, methods=['get'], url_path='resumo')
    def resumo(self, request):
        """Resumo financeiro: totais por tipo e status."""
        qs = self.filter_queryset(self.get_queryset())
        receitas  = qs.filter(tipo='receita').aggregate(total=Sum('valor'), count=Count('id'))
        despesas  = qs.filter(tipo='despesa').aggregate(total=Sum('valor'), count=Count('id'))
        pendentes = qs.filter(status='pendente').aggregate(total=Sum('valor'), count=Count('id'))
        return Response({
            'receitas':  {'total': float(receitas['total'] or 0), 'quantidade': receitas['count']},
            'despesas':  {'total': float(despesas['total'] or 0), 'quantidade': despesas['count']},
            'pendentes': {'total': float(pendentes['total'] or 0), 'quantidade': pendentes['count']},
            'saldo':     float((receitas['total'] or 0) - (despesas['total'] or 0)),
        })


# ─────────────────────────────────────────
# ESTOQUE
# ─────────────────────────────────────────

class EstoqueViewSet(viewsets.ModelViewSet):
    """ViewSet de Estoque com alertas de reposição e ajuste de quantidade."""
    queryset = Estoque.objects.all().order_by('categoria', 'nome')
    serializer_class   = EstoqueSerializer
    permission_classes = [IsAuthenticated]
    filter_backends    = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class    = EstoqueFilter
    search_fields      = ['nome', 'fornecedor', 'localizacao']
    ordering_fields    = ['nome', 'categoria', 'quantidade', 'validade']

    @action(detail=True, methods=['patch'], url_path='ajustar-quantidade')
    def ajustar_quantidade(self, request, pk=None):
        """
        Ajusta a quantidade de um item no estoque.
        Body: { "quantidade": <int>, "operacao": "adicionar" | "remover" | "definir" }
        - adicionar: incrementa a quantidade atual
        - remover: decrementa a quantidade atual (não permite ficar negativo)
        - definir: substitui a quantidade atual pelo valor fornecido
        """
        item = self.get_object()
        quantidade = request.data.get('quantidade')
        operacao   = request.data.get('operacao', 'definir')

        if quantidade is None:
            return Response(
                {'detail': 'Informe o campo "quantidade".'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            quantidade = int(quantidade)
        except (ValueError, TypeError):
            return Response(
                {'detail': 'O campo "quantidade" deve ser um número inteiro.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if quantidade < 0:
            return Response(
                {'detail': 'O campo "quantidade" deve ser positivo.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if operacao == 'adicionar':
            item.quantidade += quantidade
        elif operacao == 'remover':
            nova_qtd = item.quantidade - quantidade
            if nova_qtd < 0:
                return Response(
                    {'detail': f'Quantidade insuficiente. Estoque atual: {item.quantidade}.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            item.quantidade = nova_qtd
        elif operacao == 'definir':
            item.quantidade = quantidade
        else:
            return Response(
                {'detail': 'Operação inválida. Use "adicionar", "remover" ou "definir".'},
                status=status.HTTP_400_BAD_REQUEST
            )

        item.save(update_fields=['quantidade'])
        return Response(EstoqueSerializer(item).data)

    @action(detail=False, methods=['get'], url_path='alertas')
    def alertas(self, request):
        """Retorna itens com estoque baixo ou próximos do vencimento."""
        from django.db.models import F
        estoque_baixo = Estoque.objects.filter(
            quantidade__lte=F('quantidade_minima')
        ).order_by('quantidade')

        vencendo = Estoque.objects.filter(
            validade__isnull=False,
            validade__lte=date.today() + timedelta(days=30),
            validade__gte=date.today(),
        ).order_by('validade')

        vencidos = Estoque.objects.filter(
            validade__isnull=False,
            validade__lt=date.today(),
        ).order_by('validade')

        return Response({
            'estoque_baixo': EstoqueSerializer(estoque_baixo, many=True).data,
            'vencendo_em_30_dias': EstoqueSerializer(vencendo, many=True).data,
            'vencidos': EstoqueSerializer(vencidos, many=True).data,
        })