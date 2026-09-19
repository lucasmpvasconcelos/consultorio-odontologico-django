"""
admin.py — Painel Administrativo do Sistema Odontológico
Configurações ricas para uso real da equipe.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.db.models import F

from .models import (
    Usuario, Paciente, Dentista, Consulta,
    Prontuario, ProntuarioProcedimento,
    Procedimento, Financeiro, Estoque,
)


# ─────────────────────────────────────────
# USUÁRIO
# ─────────────────────────────────────────

@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display  = ('username', 'get_full_name', 'email', 'perfil', 'ativo', 'is_staff', 'date_joined')
    list_filter   = ('perfil', 'ativo', 'is_staff', 'is_superuser')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering      = ('username',)

    fieldsets = UserAdmin.fieldsets + (
        ('Perfil Odontológico', {'fields': ('perfil', 'ativo')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Perfil Odontológico', {'fields': ('perfil',)}),
    )

    @admin.display(boolean=True, description='Ativo')
    def ativo_display(self, obj):
        return obj.ativo


# ─────────────────────────────────────────
# PACIENTE
# ─────────────────────────────────────────

@admin.register(Paciente)
class PacienteAdmin(admin.ModelAdmin):
    list_display  = ('nome_completo', 'cpf', 'telefone', 'email', 'idade', 'plano_odonto', 'criado_em')
    list_filter   = ('plano_odonto', 'criado_em')
    search_fields = ('nome_completo', 'cpf', 'email', 'telefone')
    ordering      = ('nome_completo',)
    readonly_fields = ('criado_em', 'atualizado_em', 'idade')

    fieldsets = (
        ('Dados Pessoais', {
            'fields': ('nome_completo', 'cpf', 'data_nascimento', 'foto')
        }),
        ('Contato', {
            'fields': ('telefone', 'email', 'endereco')
        }),
        ('Convênio', {
            'fields': ('plano_odonto', 'convenio_numero'),
            'classes': ('collapse',),
        }),
        ('Saúde', {
            'fields': ('alergias', 'observacoes'),
            'classes': ('collapse',),
        }),
        ('Registro', {
            'fields': ('criado_em', 'atualizado_em'),
            'classes': ('collapse',),
        }),
    )

    @admin.display(description='Idade')
    def idade(self, obj):
        return f'{obj.idade} anos'


# ─────────────────────────────────────────
# DENTISTA
# ─────────────────────────────────────────

@admin.register(Dentista)
class DentistaAdmin(admin.ModelAdmin):
    list_display  = ('nome_completo', 'cro', 'especialidade', 'telefone', 'email', 'dias_trabalho')
    list_filter   = ('especialidade',)
    search_fields = ('nome_completo', 'cro', 'especialidade', 'email')
    ordering      = ('nome_completo',)

    fieldsets = (
        ('Dados Profissionais', {
            'fields': ('nome_completo', 'cro', 'especialidade', 'usuario')
        }),
        ('Contato', {
            'fields': ('telefone', 'email')
        }),
        ('Horário de Atendimento', {
            'fields': ('dias_trabalho', 'horario_inicio', 'horario_fim')
        }),
    )


# ─────────────────────────────────────────
# PROCEDIMENTO
# ─────────────────────────────────────────

@admin.register(Procedimento)
class ProcedimentoAdmin(admin.ModelAdmin):
    list_display  = ('nome', 'categoria', 'valor_padrao', 'duracao_media', 'codigo_tuss', 'ativo', 'ativo_badge')
    list_filter   = ('categoria', 'ativo')
    search_fields = ('nome', 'codigo_tuss', 'descricao')
    ordering      = ('categoria', 'nome')
    list_editable = ('ativo',)

    @admin.display(boolean=True, description='Ativo')
    def ativo_badge(self, obj):
        return obj.ativo


# ─────────────────────────────────────────
# CONSULTA
# ─────────────────────────────────────────

@admin.register(Consulta)
class ConsultaAdmin(admin.ModelAdmin):
    list_display  = ('paciente', 'dentista', 'data_hora', 'duracao_min', 'tipo', 'status_badge', 'confirmada')
    list_filter   = ('status', 'tipo', 'confirmada', 'data_hora', 'dentista')
    search_fields = ('paciente__nome_completo', 'paciente__cpf', 'dentista__nome_completo')
    ordering      = ('-data_hora',)
    date_hierarchy = 'data_hora'
    readonly_fields = ('criado_em',)
    autocomplete_fields = ('paciente', 'dentista')

    fieldsets = (
        ('Agendamento', {
            'fields': ('paciente', 'dentista', 'data_hora', 'duracao_min', 'tipo')
        }),
        ('Status', {
            'fields': ('status', 'confirmada', 'observacoes')
        }),
        ('Registro', {
            'fields': ('criado_em',),
            'classes': ('collapse',),
        }),
    )

    @admin.display(description='Status')
    def status_badge(self, obj):
        cores = {
            'agendada':   '#3b82f6',
            'confirmada': '#22c55e',
            'realizada':  '#6b7280',
            'cancelada':  '#ef4444',
            'falta':      '#f59e0b',
        }
        cor = cores.get(obj.status, '#6b7280')
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;border-radius:4px;font-size:11px">{}</span>',
            cor, obj.get_status_display()
        )


# ─────────────────────────────────────────
# PRONTUÁRIO
# ─────────────────────────────────────────

class ProntuarioProcedimentoInline(admin.TabularInline):
    model  = ProntuarioProcedimento
    extra  = 0
    fields = ('procedimento', 'quantidade', 'valor_cobrado', 'dente', 'observacao')
    autocomplete_fields = ('procedimento',)


@admin.register(Prontuario)
class ProntuarioAdmin(admin.ModelAdmin):
    list_display   = ('id', 'paciente', 'dentista', 'data_atendimento', 'proxima_consulta')
    list_filter    = ('data_atendimento', 'dentista')
    search_fields  = ('paciente__nome_completo', 'paciente__cpf', 'diagnostico')
    ordering       = ('-data_atendimento',)
    date_hierarchy = 'data_atendimento'
    readonly_fields = ('criado_em',)
    inlines        = [ProntuarioProcedimentoInline]
    autocomplete_fields = ('paciente', 'dentista')

    fieldsets = (
        ('Identificação', {
            'fields': ('paciente', 'dentista', 'consulta', 'data_atendimento')
        }),
        ('Clínico', {
            'fields': ('anamnese', 'diagnostico', 'tratamento_plano', 'prescricao')
        }),
        ('Arquivos', {
            'fields': ('radiografia', 'odontograma'),
            'classes': ('collapse',),
        }),
        ('Acompanhamento', {
            'fields': ('proxima_consulta', 'criado_em'),
        }),
    )


# ─────────────────────────────────────────
# FINANCEIRO
# ─────────────────────────────────────────

@admin.register(Financeiro)
class FinanceiroAdmin(admin.ModelAdmin):
    list_display  = ('descricao', 'tipo_badge', 'valor', 'desconto', 'valor_liquido',
                     'forma_pagamento', 'status', 'vencimento', 'pago_em')
    list_filter   = ('tipo', 'status', 'forma_pagamento', 'vencimento')
    search_fields = ('descricao', 'paciente__nome_completo')
    ordering      = ('-criado_em',)
    date_hierarchy = 'criado_em'
    readonly_fields = ('criado_em', 'valor_liquido')
    autocomplete_fields = ('paciente',)

    fieldsets = (
        ('Lançamento', {
            'fields': ('tipo', 'descricao', 'paciente', 'consulta')
        }),
        ('Valores', {
            'fields': ('valor', 'desconto', 'valor_liquido')
        }),
        ('Pagamento', {
            'fields': ('forma_pagamento', 'status', 'vencimento', 'pago_em', 'parcelas', 'parcela_atual')
        }),
        ('Extras', {
            'fields': ('comprovante', 'observacoes', 'criado_em'),
            'classes': ('collapse',),
        }),
    )

    @admin.display(description='Tipo')
    def tipo_badge(self, obj):
        cor = '#22c55e' if obj.tipo == 'receita' else '#ef4444'
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;border-radius:4px;font-size:11px">{}</span>',
            cor, obj.get_tipo_display()
        )


# ─────────────────────────────────────────
# ESTOQUE
# ─────────────────────────────────────────

@admin.register(Estoque)
class EstoqueAdmin(admin.ModelAdmin):
    list_display  = ('nome', 'categoria', 'quantidade', 'quantidade_minima',
                     'unidade', 'fornecedor', 'validade', 'alerta_estoque')
    list_filter   = ('categoria', 'fornecedor', 'validade')
    search_fields = ('nome', 'fornecedor', 'localizacao')
    ordering      = ('categoria', 'nome')
    readonly_fields = ('criado_em', 'atualizado_em', 'estoque_baixo')

    @admin.display(boolean=True, description='⚠️ Estoque baixo')
    def alerta_estoque(self, obj):
        return obj.estoque_baixo