"""
filters.py — FilterSets para todos os módulos da API
Django REST Framework + django-filter
"""

import django_filters
from .models import Paciente, Consulta, Financeiro, Estoque, Dentista, Procedimento, Prontuario


class PacienteFilter(django_filters.FilterSet):
    """Filtros para listagem de Pacientes."""
    nome           = django_filters.CharFilter(field_name='nome_completo', lookup_expr='icontains', label='Nome')
    cpf            = django_filters.CharFilter(lookup_expr='icontains', label='CPF')
    email          = django_filters.CharFilter(lookup_expr='icontains', label='E-mail')
    plano          = django_filters.CharFilter(field_name='plano_odonto', lookup_expr='icontains', label='Plano')
    nascimento_de  = django_filters.DateFilter(field_name='data_nascimento', lookup_expr='gte', label='Nascimento a partir de')
    nascimento_ate = django_filters.DateFilter(field_name='data_nascimento', lookup_expr='lte', label='Nascimento até')
    criado_de      = django_filters.DateTimeFilter(field_name='criado_em', lookup_expr='gte', label='Cadastrado a partir de')
    criado_ate     = django_filters.DateTimeFilter(field_name='criado_em', lookup_expr='lte', label='Cadastrado até')
    tem_convenio   = django_filters.BooleanFilter(field_name='plano_odonto', lookup_expr='isnull', exclude=True, label='Possui convênio')

    class Meta:
        model  = Paciente
        fields = ['nome', 'cpf', 'email', 'plano', 'nascimento_de', 'nascimento_ate', 'criado_de', 'criado_ate']


class ConsultaFilter(django_filters.FilterSet):
    """Filtros para listagem de Consultas."""
    paciente_nome  = django_filters.CharFilter(field_name='paciente__nome_completo', lookup_expr='icontains', label='Nome do paciente')
    paciente_id    = django_filters.NumberFilter(field_name='paciente__id', label='ID do paciente')
    dentista_id    = django_filters.NumberFilter(field_name='dentista__id', label='ID do dentista')
    status         = django_filters.ChoiceFilter(choices=Consulta.Status.choices, label='Status')
    tipo           = django_filters.ChoiceFilter(choices=Consulta.Tipo.choices, label='Tipo')
    data_de        = django_filters.DateTimeFilter(field_name='data_hora', lookup_expr='gte', label='Data/hora a partir de')
    data_ate       = django_filters.DateTimeFilter(field_name='data_hora', lookup_expr='lte', label='Data/hora até')
    confirmada     = django_filters.BooleanFilter(label='Confirmada')

    class Meta:
        model  = Consulta
        fields = ['paciente_id', 'dentista_id', 'status', 'tipo', 'confirmada']


class FinanceiroFilter(django_filters.FilterSet):
    """Filtros para listagem de Lançamentos Financeiros."""
    paciente_nome   = django_filters.CharFilter(field_name='paciente__nome_completo', lookup_expr='icontains', label='Nome do paciente')
    tipo            = django_filters.ChoiceFilter(choices=Financeiro.Tipo.choices, label='Tipo (receita/despesa)')
    status          = django_filters.ChoiceFilter(choices=Financeiro.Status.choices, label='Status')
    forma_pagamento = django_filters.ChoiceFilter(choices=Financeiro.FormaPagamento.choices, label='Forma de pagamento')
    vencimento_de   = django_filters.DateFilter(field_name='vencimento', lookup_expr='gte', label='Vencimento a partir de')
    vencimento_ate  = django_filters.DateFilter(field_name='vencimento', lookup_expr='lte', label='Vencimento até')
    valor_min       = django_filters.NumberFilter(field_name='valor', lookup_expr='gte', label='Valor mínimo')
    valor_max       = django_filters.NumberFilter(field_name='valor', lookup_expr='lte', label='Valor máximo')
    criado_de       = django_filters.DateTimeFilter(field_name='criado_em', lookup_expr='gte', label='Criado a partir de')
    criado_ate      = django_filters.DateTimeFilter(field_name='criado_em', lookup_expr='lte', label='Criado até')

    class Meta:
        model  = Financeiro
        fields = ['tipo', 'status', 'forma_pagamento', 'vencimento_de', 'vencimento_ate']


class EstoqueFilter(django_filters.FilterSet):
    """Filtros para listagem de Estoque."""
    nome           = django_filters.CharFilter(lookup_expr='icontains', label='Nome do item')
    categoria      = django_filters.ChoiceFilter(choices=Estoque.Categoria.choices, label='Categoria')
    fornecedor     = django_filters.CharFilter(lookup_expr='icontains', label='Fornecedor')
    estoque_baixo  = django_filters.BooleanFilter(method='filter_estoque_baixo', label='Apenas estoque baixo')
    validade_de    = django_filters.DateFilter(field_name='validade', lookup_expr='gte', label='Validade a partir de')
    validade_ate   = django_filters.DateFilter(field_name='validade', lookup_expr='lte', label='Validade até')

    class Meta:
        model  = Estoque
        fields = ['nome', 'categoria', 'fornecedor']

    def filter_estoque_baixo(self, queryset, name, value):
        """Filtra itens com quantidade <= quantidade_minima."""
        if value:
            from django.db.models import F
            return queryset.filter(quantidade__lte=F('quantidade_minima'))
        return queryset


class DentistaFilter(django_filters.FilterSet):
    """Filtros para listagem de Dentistas."""
    nome           = django_filters.CharFilter(field_name='nome_completo', lookup_expr='icontains', label='Nome')
    especialidade  = django_filters.CharFilter(lookup_expr='icontains', label='Especialidade')

    class Meta:
        model  = Dentista
        fields = ['nome', 'especialidade']


class ProcedimentoFilter(django_filters.FilterSet):
    """Filtros para listagem de Procedimentos."""
    nome      = django_filters.CharFilter(lookup_expr='icontains', label='Nome')
    categoria = django_filters.ChoiceFilter(choices=Procedimento.Categoria.choices, label='Categoria')
    ativo     = django_filters.BooleanFilter(label='Ativo')
    valor_min = django_filters.NumberFilter(field_name='valor_padrao', lookup_expr='gte', label='Valor mínimo')
    valor_max = django_filters.NumberFilter(field_name='valor_padrao', lookup_expr='lte', label='Valor máximo')

    class Meta:
        model  = Procedimento
        fields = ['nome', 'categoria', 'ativo']


class ProntuarioFilter(django_filters.FilterSet):
    """Filtros avançados para listagem de Prontuários."""
    paciente_id    = django_filters.NumberFilter(field_name='paciente__id', label='ID do paciente')
    paciente_nome  = django_filters.CharFilter(field_name='paciente__nome_completo', lookup_expr='icontains', label='Nome do paciente')
    dentista_id    = django_filters.NumberFilter(field_name='dentista__id', label='ID do dentista')
    data_de        = django_filters.DateFilter(field_name='data_atendimento', lookup_expr='gte', label='Atendimento a partir de')
    data_ate       = django_filters.DateFilter(field_name='data_atendimento', lookup_expr='lte', label='Atendimento até')
    diagnostico    = django_filters.CharFilter(lookup_expr='icontains', label='Diagnóstico')
    tem_radiografia = django_filters.BooleanFilter(field_name='radiografia', lookup_expr='isnull', exclude=True, label='Possui radiografia')

    class Meta:
        model  = Prontuario
        fields = ['paciente_id', 'dentista_id', 'data_atendimento']
