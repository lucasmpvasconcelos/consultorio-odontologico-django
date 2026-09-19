"""
serializers.py — Sistema de Gestão Odontológica
Django REST Framework — serializers com validações robustas
"""

import re
from datetime import date, timedelta

from django.contrib.auth.password_validation import validate_password
from django.utils import timezone
from rest_framework import serializers

from .models import (
    Usuario, Paciente, Dentista, Consulta,
    Prontuario, Procedimento, ProntuarioProcedimento,
    Financeiro, Estoque,
)


# ─────────────────────────────────────────
# USUÁRIO
# ─────────────────────────────────────────

class UsuarioSerializer(serializers.ModelSerializer):
    """Serializer de leitura/atualização de usuário (sem senha)."""

    class Meta:
        model  = Usuario
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'perfil', 'ativo', 'date_joined']
        read_only_fields = ['id', 'date_joined']


class UsuarioCreateSerializer(serializers.ModelSerializer):
    """Serializer para criação de usuário com senha segura."""
    password  = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    password2 = serializers.CharField(write_only=True, required=True, label='Confirmar senha', style={'input_type': 'password'})

    class Meta:
        model  = Usuario
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'perfil', 'password', 'password2']
        read_only_fields = ['id']

    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError({'password2': 'As senhas não coincidem.'})
        validate_password(data['password'])
        return data

    def create(self, validated_data):
        validated_data.pop('password2')
        password = validated_data.pop('password')
        user = Usuario(**validated_data)
        user.set_password(password)
        user.save()
        return user


# ─────────────────────────────────────────
# PACIENTE
# ─────────────────────────────────────────

class PacienteListSerializer(serializers.ModelSerializer):
    """Serializer resumido para listagem de pacientes."""
    idade = serializers.ReadOnlyField()

    class Meta:
        model  = Paciente
        fields = [
            'id', 'nome_completo', 'cpf', 'data_nascimento',
            'idade', 'telefone', 'email', 'plano_odonto', 'criado_em',
        ]


class PacienteDetailSerializer(serializers.ModelSerializer):
    """Serializer completo para criação, edição e detalhe de paciente."""
    idade           = serializers.ReadOnlyField()
    total_consultas = serializers.SerializerMethodField()
    ultima_consulta = serializers.SerializerMethodField()

    class Meta:
        model  = Paciente
        fields = '__all__'
        read_only_fields = ['criado_em', 'atualizado_em']

    def get_total_consultas(self, obj):
        return obj.consultas.count()

    def get_ultima_consulta(self, obj):
        ultima = obj.consultas.order_by('-data_hora').first()
        if ultima:
            return {
                'id':       ultima.id,
                'data_hora': ultima.data_hora,
                'status':   ultima.get_status_display(),
                'dentista': str(ultima.dentista),
            }
        return None

    def validate_cpf(self, value):
        """Valida e formata CPF (aceita com ou sem formatação)."""
        cpf = re.sub(r'\D', '', value)
        if len(cpf) != 11:
            raise serializers.ValidationError('CPF deve ter 11 dígitos.')
        if cpf == cpf[0] * 11:
            raise serializers.ValidationError('CPF inválido (todos dígitos iguais).')
        # Validação dos dígitos verificadores
        for i in range(9, 11):
            soma = sum(int(cpf[j]) * (i + 1 - j) for j in range(i))
            digito = (soma * 10 % 11) % 10
            if digito != int(cpf[i]):
                raise serializers.ValidationError('CPF inválido.')
        return f'{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}'

    def validate_data_nascimento(self, value):
        if value > date.today():
            raise serializers.ValidationError('Data de nascimento não pode ser futura.')
        if value.year < 1900:
            raise serializers.ValidationError('Data de nascimento inválida.')
        return value


# ─────────────────────────────────────────
# DENTISTA
# ─────────────────────────────────────────

class DentistaSerializer(serializers.ModelSerializer):
    """Serializer completo de Dentista."""
    dias_trabalho_lista = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model  = Dentista
        fields = '__all__'
        read_only_fields = ['id']

    def get_dias_trabalho_lista(self, obj):
        if obj.dias_trabalho:
            return [d.strip() for d in obj.dias_trabalho.split(',')]
        return []

    def validate_cro(self, value):
        value = value.strip().upper()
        if not re.match(r'^[A-Z]{2}-\d{4,6}$', value):
            raise serializers.ValidationError('CRO inválido. Use o formato UF-XXXXX (ex: SP-12345).')
        return value


# ─────────────────────────────────────────
# PROCEDIMENTO
# ─────────────────────────────────────────

class ProcedimentoSerializer(serializers.ModelSerializer):
    """Serializer de Procedimento."""
    categoria_display = serializers.CharField(source='get_categoria_display', read_only=True)

    class Meta:
        model  = Procedimento
        fields = '__all__'
        read_only_fields = ['id']

    def validate_valor_padrao(self, value):
        if value <= 0:
            raise serializers.ValidationError('O valor deve ser positivo.')
        return value

    def validate_duracao_media(self, value):
        if value <= 0:
            raise serializers.ValidationError('A duração deve ser positiva.')
        return value


# ─────────────────────────────────────────
# CONSULTA
# ─────────────────────────────────────────

class ConsultaResumoSerializer(serializers.ModelSerializer):
    """Resumo de consultas (para listagem no paciente)."""
    dentista_nome  = serializers.CharField(source='dentista.nome_completo', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    tipo_display   = serializers.CharField(source='get_tipo_display',   read_only=True)

    class Meta:
        model  = Consulta
        fields = [
            'id', 'data_hora', 'duracao_min', 'status', 'status_display',
            'tipo', 'tipo_display', 'dentista_nome', 'confirmada', 'observacoes',
        ]


class ConsultaSerializer(serializers.ModelSerializer):
    """Serializer completo de Consulta com validação de conflitos de agenda."""
    paciente_nome  = serializers.CharField(source='paciente.nome_completo', read_only=True)
    dentista_nome  = serializers.CharField(source='dentista.nome_completo', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    tipo_display   = serializers.CharField(source='get_tipo_display',   read_only=True)
    data_fim       = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model  = Consulta
        fields = '__all__'
        read_only_fields = ['id', 'criado_em']

    def get_data_fim(self, obj):
        """Calcula horário de término da consulta."""
        return obj.data_hora + timedelta(minutes=obj.duracao_min)

    def validate(self, data):
        """Verifica conflito de horário para o dentista."""
        dentista  = data.get('dentista') or (self.instance.dentista if self.instance else None)
        data_hora = data.get('data_hora') or (self.instance.data_hora if self.instance else None)
        duracao   = data.get('duracao_min') if 'duracao_min' in data else (
            self.instance.duracao_min if self.instance else 60
        )
        status    = data.get('status', self.instance.status if self.instance else 'agendada')

        if dentista and data_hora and status not in ('cancelada', 'falta'):
            data_fim = data_hora + timedelta(minutes=duracao)

            # Busca consultas do dentista que se sobrepõem ao intervalo [data_hora, data_fim)
            conflitos = Consulta.objects.filter(
                dentista=dentista,
                status__in=['agendada', 'confirmada'],
                data_hora__lt=data_fim,
                # A consulta existente termina depois que a nova começa:
                # data_hora_existente + duracao_existente > data_hora_nova
                # => filtrado em Python abaixo para suportar SQLite
            ).exclude(
                data_hora__gte=data_fim
            )

            # Exclui o próprio registro em caso de update
            if self.instance:
                conflitos = conflitos.exclude(pk=self.instance.pk)

            # Verifica sobreposição real (fim da consulta existente > início da nova)
            conflitos_reais = [
                c for c in conflitos
                if c.data_hora + timedelta(minutes=c.duracao_min) > data_hora
            ]

            if conflitos_reais:
                c = conflitos_reais[0]
                raise serializers.ValidationError({
                    'data_hora': (
                        f'Conflito de agenda: {dentista.nome_completo} já tem '
                        f'consulta marcada às {c.data_hora.strftime("%d/%m/%Y %H:%M")} '
                        f'com duração de {c.duracao_min} min.'
                    )
                })
        return data


# ─────────────────────────────────────────
# PRONTUÁRIO
# ─────────────────────────────────────────

class ProntuarioProcedimentoSerializer(serializers.ModelSerializer):
    """Procedimentos de um prontuário."""
    procedimento_nome = serializers.CharField(source='procedimento.nome', read_only=True)

    class Meta:
        model  = ProntuarioProcedimento
        fields = '__all__'
        read_only_fields = ['id']

    def validate(self, data):
        """
        Valida unicidade de (prontuario, procedimento, dente) mesmo quando dente é None,
        pois unique_together não funciona com campos nullable no nível do banco.
        """
        prontuario   = data.get('prontuario') or (self.instance.prontuario if self.instance else None)
        procedimento = data.get('procedimento') or (self.instance.procedimento if self.instance else None)
        dente        = data.get('dente') or (self.instance.dente if self.instance else None)

        if prontuario and procedimento:
            qs = ProntuarioProcedimento.objects.filter(
                prontuario=prontuario,
                procedimento=procedimento,
                dente=dente,
            )
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                dente_str = f'dente {dente}' if dente else 'sem dente especificado'
                raise serializers.ValidationError(
                    f'Este procedimento já está registrado neste prontuário ({dente_str}).'
                )
        return data


class ProntuarioResumoSerializer(serializers.ModelSerializer):
    """Resumo de prontuário (para listagem no paciente)."""
    dentista_nome = serializers.CharField(source='dentista.nome_completo', read_only=True)

    class Meta:
        model  = Prontuario
        fields = [
            'id', 'data_atendimento', 'diagnostico',
            'dentista_nome', 'proxima_consulta',
        ]


class ProntuarioSerializer(serializers.ModelSerializer):
    """Serializer completo de Prontuário."""
    paciente_nome    = serializers.CharField(source='paciente.nome_completo', read_only=True)
    dentista_nome    = serializers.CharField(source='dentista.nome_completo', read_only=True)
    procedimentos_detail = ProntuarioProcedimentoSerializer(
        source='prontuarioprocedimento_set', many=True, read_only=True
    )

    class Meta:
        model  = Prontuario
        fields = '__all__'
        read_only_fields = ['id', 'criado_em']

    def validate_data_atendimento(self, value):
        if value > date.today():
            raise serializers.ValidationError('Data de atendimento não pode ser futura.')
        return value


# ─────────────────────────────────────────
# FINANCEIRO
# ─────────────────────────────────────────

class FinanceiroSerializer(serializers.ModelSerializer):
    """Serializer de Lançamento Financeiro."""
    paciente_nome        = serializers.CharField(source='paciente.nome_completo', read_only=True)
    tipo_display         = serializers.CharField(source='get_tipo_display',         read_only=True)
    status_display       = serializers.CharField(source='get_status_display',       read_only=True)
    forma_pagamento_display = serializers.CharField(source='get_forma_pagamento_display', read_only=True)
    valor_liquido        = serializers.ReadOnlyField()

    class Meta:
        model  = Financeiro
        fields = '__all__'
        read_only_fields = ['id', 'criado_em']

    def validate_valor(self, value):
        if value <= 0:
            raise serializers.ValidationError('O valor deve ser positivo.')
        return value

    def validate_desconto(self, value):
        """Garante que o desconto não seja negativo."""
        if value < 0:
            raise serializers.ValidationError('O desconto não pode ser negativo.')
        return value

    def validate(self, data):
        valor    = data.get('valor', getattr(self.instance, 'valor', 0))
        desconto = data.get('desconto', getattr(self.instance, 'desconto', 0))
        if desconto > valor:
            raise serializers.ValidationError({'desconto': 'O desconto não pode ser maior que o valor.'})
        return data

    def validate_parcelas(self, value):
        if value < 1:
            raise serializers.ValidationError('O número de parcelas deve ser ao menos 1.')
        return value


# ─────────────────────────────────────────
# ESTOQUE
# ─────────────────────────────────────────

class EstoqueSerializer(serializers.ModelSerializer):
    """Serializer de Item de Estoque."""
    categoria_display = serializers.CharField(source='get_categoria_display', read_only=True)
    estoque_baixo     = serializers.ReadOnlyField()
    dias_para_vencer  = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model  = Estoque
        fields = '__all__'
        read_only_fields = ['id', 'criado_em', 'atualizado_em']

    def get_dias_para_vencer(self, obj):
        if obj.validade:
            return (obj.validade - date.today()).days
        return None

    def validate_quantidade(self, value):
        if value < 0:
            raise serializers.ValidationError('A quantidade não pode ser negativa.')
        return value
