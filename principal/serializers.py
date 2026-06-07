"""
serializers.py — Módulo Pacientes
Django REST Framework
"""
 
from rest_framework import serializers
from .models import Paciente, Consulta, Prontuario
 
 
class PacienteListSerializer(serializers.ModelSerializer):
    """Serializer resumido para listagem."""
    idade = serializers.ReadOnlyField()
 
    class Meta:
        model = Paciente
        fields = [
            'id', 'nome_completo', 'cpf', 'data_nascimento',
            'idade', 'telefone', 'email', 'plano_odonto', 'criado_em',
        ]
 
 
class PacienteDetailSerializer(serializers.ModelSerializer):
    """Serializer completo para criação/edição/detalhe."""
    idade = serializers.ReadOnlyField()
    total_consultas = serializers.SerializerMethodField()
    ultima_consulta = serializers.SerializerMethodField()
 
    class Meta:
        model = Paciente
        fields = '__all__'
        read_only_fields = ['criado_em', 'atualizado_em']
 
    def get_total_consultas(self, obj):
        return obj.consultas.count()
 
    def get_ultima_consulta(self, obj):
        ultima = obj.consultas.order_by('-data_hora').first()
        if ultima:
            return {
                'id': ultima.id,
                'data_hora': ultima.data_hora,
                'status': ultima.get_status_display(),
                'dentista': str(ultima.dentista),
            }
        return None
 
    def validate_cpf(self, value):
        import re
        cpf = re.sub(r'\D', '', value)
        if len(cpf) != 11:
            raise serializers.ValidationError('CPF deve ter 11 dígitos.')
        # Verifica dígitos repetidos
        if cpf == cpf[0] * 11:
            raise serializers.ValidationError('CPF inválido.')
        # Validação dos dígitos verificadores
        for i in range(9, 11):
            soma = sum(int(cpf[j]) * (i + 1 - j) for j in range(i))
            digito = (soma * 10 % 11) % 10
            if digito != int(cpf[i]):
                raise serializers.ValidationError('CPF inválido.')
        # Formata
        return f'{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}'
 
    def validate_data_nascimento(self, value):
        from datetime import date
        if value > date.today():
            raise serializers.ValidationError('Data de nascimento não pode ser futura.')
        return value
 
 
class ConsultaResumoSerializer(serializers.ModelSerializer):
    """Consultas do paciente (somente leitura)."""
    dentista_nome = serializers.CharField(source='dentista.nome_completo', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    tipo_display   = serializers.CharField(source='get_tipo_display',   read_only=True)
 
    class Meta:
        model = Consulta
        fields = [
            'id', 'data_hora', 'duracao_min', 'status', 'status_display',
            'tipo', 'tipo_display', 'dentista_nome', 'confirmada', 'observacoes',
        ]
 
 
class ProntuarioResumoSerializer(serializers.ModelSerializer):
    """Prontuários do paciente (somente leitura)."""
    dentista_nome = serializers.CharField(source='dentista.nome_completo', read_only=True)
 
    class Meta:
        model = Prontuario
        fields = [
            'id', 'data_atendimento', 'diagnostico',
            'dentista_nome', 'proxima_consulta',
        ]