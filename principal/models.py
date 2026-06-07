"""
models.py — Sistema de Gestão Odontológica
Django 4.x+ | PostgreSQL recomendado
"""
 
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
 
 
# ─────────────────────────────────────────
# USUÁRIO (Autenticação)
# ─────────────────────────────────────────
 
class Usuario(AbstractUser):
    class Perfil(models.TextChoices):
        ADMIN       = 'admin',       'Administrador'
        DENTISTA    = 'dentista',    'Dentista'
        RECEPCIONISTA = 'recepcionista', 'Recepcionista'
 
    perfil = models.CharField(max_length=20, choices=Perfil.choices, default=Perfil.RECEPCIONISTA)
    ativo  = models.BooleanField(default=True)
 
    class Meta:
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'
 
    def __str__(self):
        return f"{self.get_full_name()} ({self.get_perfil_display()})"
 
 
# ─────────────────────────────────────────
# PACIENTE
# ─────────────────────────────────────────
 
class Paciente(models.Model):
    cpf_validator = RegexValidator(r'^\d{3}\.\d{3}\.\d{3}-\d{2}$', 'CPF inválido.')
 
    nome_completo   = models.CharField(max_length=200)
    cpf             = models.CharField(max_length=14, unique=True, validators=[cpf_validator])
    data_nascimento = models.DateField()
    telefone        = models.CharField(max_length=20)
    email           = models.EmailField(blank=True, null=True)
    endereco        = models.TextField(blank=True, null=True)
 
    # Convênio
    plano_odonto    = models.CharField(max_length=100, blank=True, null=True, verbose_name='Plano Odontológico')
    convenio_numero = models.CharField(max_length=50,  blank=True, null=True, verbose_name='Nº do Convênio')
 
    # Saúde
    alergias        = models.TextField(blank=True, null=True)
    observacoes     = models.TextField(blank=True, null=True)
    foto            = models.ImageField(upload_to='pacientes/fotos/', blank=True, null=True)
 
    criado_em       = models.DateTimeField(auto_now_add=True)
    atualizado_em   = models.DateTimeField(auto_now=True)
 
    class Meta:
        verbose_name = 'Paciente'
        verbose_name_plural = 'Pacientes'
        ordering = ['nome_completo']
 
    def __str__(self):
        return self.nome_completo
 
    @property
    def idade(self):
        from datetime import date
        today = date.today()
        return today.year - self.data_nascimento.year - (
            (today.month, today.day) < (self.data_nascimento.month, self.data_nascimento.day)
        )
 
 
# ─────────────────────────────────────────
# DENTISTA
# ─────────────────────────────────────────
 
class Dentista(models.Model):
    class DiaSemana(models.TextChoices):
        SEG = 'SEG', 'Segunda'
        TER = 'TER', 'Terça'
        QUA = 'QUA', 'Quarta'
        QUI = 'QUI', 'Quinta'
        SEX = 'SEX', 'Sexta'
        SAB = 'SAB', 'Sábado'
 
    usuario         = models.OneToOneField(Usuario, on_delete=models.SET_NULL, null=True, blank=True)
    nome_completo   = models.CharField(max_length=200)
    cro             = models.CharField(max_length=20, unique=True, verbose_name='CRO')
    especialidade   = models.CharField(max_length=100)
    telefone        = models.CharField(max_length=20)
    email           = models.EmailField(blank=True, null=True)
    horario_inicio  = models.TimeField(blank=True, null=True)
    horario_fim     = models.TimeField(blank=True, null=True)
    dias_trabalho   = models.CharField(
        max_length=30, blank=True, null=True,
        help_text='Ex: SEG,TER,QUA,QUI,SEX'
    )
 
    class Meta:
        verbose_name = 'Dentista'
        verbose_name_plural = 'Dentistas'
        ordering = ['nome_completo']
 
    def __str__(self):
        return f"Dr(a). {self.nome_completo} — {self.especialidade}"
 
 
# ─────────────────────────────────────────
# PROCEDIMENTO (Catálogo)
# ─────────────────────────────────────────
 
class Procedimento(models.Model):
    class Categoria(models.TextChoices):
        PREVENTIVO   = 'preventivo',   'Preventivo'
        RESTAURADOR  = 'restaurador',  'Restaurador'
        ENDODONTIA   = 'endodontia',   'Endodontia'
        PERIODONTIA  = 'periodontia',  'Periodontia'
        ORTODONTIA   = 'ortodontia',   'Ortodontia'
        IMPLANTE     = 'implante',     'Implante'
        CIRURGIA     = 'cirurgia',     'Cirurgia'
        ESTETICO     = 'estetico',     'Estético'
        PEDIATRICO   = 'pediatrico',   'Pediátrico'
        OUTRO        = 'outro',        'Outro'
 
    nome          = models.CharField(max_length=150)
    categoria     = models.CharField(max_length=20, choices=Categoria.choices)
    valor_padrao  = models.DecimalField(max_digits=10, decimal_places=2)
    descricao     = models.TextField(blank=True, null=True)
    duracao_media = models.IntegerField(default=60, help_text='Duração em minutos')
    codigo_tuss   = models.CharField(max_length=20, blank=True, null=True, verbose_name='Código TUSS')
    ativo         = models.BooleanField(default=True)
 
    class Meta:
        verbose_name = 'Procedimento'
        verbose_name_plural = 'Procedimentos'
        ordering = ['categoria', 'nome']
 
    def __str__(self):
        return f"{self.nome} (R$ {self.valor_padrao})"
 
 
# ─────────────────────────────────────────
# CONSULTA (Agendamento)
# ─────────────────────────────────────────
 
class Consulta(models.Model):
    class Status(models.TextChoices):
        AGENDADA   = 'agendada',   'Agendada'
        CONFIRMADA = 'confirmada', 'Confirmada'
        REALIZADA  = 'realizada',  'Realizada'
        CANCELADA  = 'cancelada',  'Cancelada'
        FALTA      = 'falta',      'Falta (não compareceu)'
 
    class Tipo(models.TextChoices):
        CONSULTA    = 'consulta',    'Consulta'
        RETORNO     = 'retorno',     'Retorno'
        EMERGENCIA  = 'emergencia',  'Emergência'
        AVALIACAO   = 'avaliacao',   'Avaliação'
 
    paciente     = models.ForeignKey(Paciente, on_delete=models.PROTECT, related_name='consultas')
    dentista     = models.ForeignKey(Dentista, on_delete=models.PROTECT, related_name='consultas')
    data_hora    = models.DateTimeField()
    duracao_min  = models.IntegerField(default=60, verbose_name='Duração (min)')
    status       = models.CharField(max_length=15, choices=Status.choices, default=Status.AGENDADA)
    tipo         = models.CharField(max_length=15, choices=Tipo.choices, default=Tipo.CONSULTA)
    confirmada   = models.BooleanField(default=False)
    observacoes  = models.TextField(blank=True, null=True)
    criado_em    = models.DateTimeField(auto_now_add=True)
 
    class Meta:
        verbose_name = 'Consulta'
        verbose_name_plural = 'Consultas'
        ordering = ['data_hora']
 
    def __str__(self):
        return f"{self.paciente} — {self.data_hora.strftime('%d/%m/%Y %H:%M')} ({self.get_status_display()})"
 
 
# ─────────────────────────────────────────
# PRONTUÁRIO
# ─────────────────────────────────────────
 
class Prontuario(models.Model):
    paciente          = models.ForeignKey(Paciente,   on_delete=models.PROTECT, related_name='prontuarios')
    consulta          = models.OneToOneField(Consulta, on_delete=models.SET_NULL, null=True, blank=True)
    dentista          = models.ForeignKey(Dentista,   on_delete=models.PROTECT, related_name='prontuarios')
    data_atendimento  = models.DateField()
    anamnese          = models.TextField()
    diagnostico       = models.TextField()
    tratamento_plano  = models.TextField(blank=True, null=True, verbose_name='Plano de Tratamento')
    prescricao        = models.TextField(blank=True, null=True, verbose_name='Prescrição')
    radiografia       = models.FileField(upload_to='prontuarios/radiografias/', blank=True, null=True)
    # Odontograma: dict com estado de cada dente, ex: {"18": "carie", "11": "restaurado"}
    odontograma       = models.JSONField(default=dict, blank=True)
    proxima_consulta  = models.DateField(blank=True, null=True, verbose_name='Próxima Consulta')
    procedimentos     = models.ManyToManyField(
        Procedimento,
        through='ProntuarioProcedimento',
        related_name='prontuarios'
    )
    criado_em         = models.DateTimeField(auto_now_add=True)
 
    class Meta:
        verbose_name = 'Prontuário'
        verbose_name_plural = 'Prontuários'
        ordering = ['-data_atendimento']
 
    def __str__(self):
        return f"Prontuário #{self.pk} — {self.paciente} em {self.data_atendimento}"
 
 
class ProntuarioProcedimento(models.Model):
    """Tabela intermediária M2M: Prontuário ↔ Procedimento"""
    prontuario   = models.ForeignKey(Prontuario,  on_delete=models.CASCADE)
    procedimento = models.ForeignKey(Procedimento, on_delete=models.PROTECT)
    quantidade   = models.IntegerField(default=1)
    valor_cobrado = models.DecimalField(max_digits=10, decimal_places=2, help_text='Pode diferir do valor padrão')
    dente        = models.CharField(max_length=10, blank=True, null=True, help_text='Número do dente (ex: 11, 36)')
    observacao   = models.CharField(max_length=255, blank=True, null=True)
 
    class Meta:
        verbose_name = 'Procedimento do Prontuário'
        unique_together = ('prontuario', 'procedimento', 'dente')
 
    def __str__(self):
        return f"{self.procedimento.nome} — Dente {self.dente or 'N/A'}"
 
 
# ─────────────────────────────────────────
# FINANCEIRO (Lançamentos)
# ─────────────────────────────────────────
 
class Financeiro(models.Model):
    class Tipo(models.TextChoices):
        RECEITA  = 'receita',  'Receita'
        DESPESA  = 'despesa',  'Despesa'
 
    class Status(models.TextChoices):
        PENDENTE = 'pendente', 'Pendente'
        PAGO     = 'pago',     'Pago'
        CANCELADO = 'cancelado', 'Cancelado'
        ATRASADO = 'atrasado', 'Atrasado'
 
    class FormaPagamento(models.TextChoices):
        DINHEIRO  = 'dinheiro',  'Dinheiro'
        CARTAO_DB = 'debito',    'Cartão de Débito'
        CARTAO_CR = 'credito',   'Cartão de Crédito'
        PIX       = 'pix',       'PIX'
        BOLETO    = 'boleto',    'Boleto'
        CONVENIO  = 'convenio',  'Convênio'
        OUTRO     = 'outro',     'Outro'
 
    paciente       = models.ForeignKey(Paciente, on_delete=models.PROTECT, related_name='lancamentos', null=True, blank=True)
    consulta       = models.ForeignKey(Consulta, on_delete=models.SET_NULL,  related_name='lancamentos', null=True, blank=True)
    tipo           = models.CharField(max_length=10, choices=Tipo.choices)
    descricao      = models.CharField(max_length=255)
    valor          = models.DecimalField(max_digits=10, decimal_places=2)
    desconto       = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status         = models.CharField(max_length=15, choices=Status.choices, default=Status.PENDENTE)
    forma_pagamento = models.CharField(max_length=15, choices=FormaPagamento.choices, default=FormaPagamento.DINHEIRO)
    vencimento     = models.DateField(blank=True, null=True)
    pago_em        = models.DateField(blank=True, null=True)
    parcelas       = models.IntegerField(default=1)
    parcela_atual  = models.IntegerField(default=1)
    comprovante    = models.FileField(upload_to='financeiro/comprovantes/', blank=True, null=True)
    observacoes    = models.TextField(blank=True, null=True)
    criado_em      = models.DateTimeField(auto_now_add=True)
 
    class Meta:
        verbose_name = 'Lançamento Financeiro'
        verbose_name_plural = 'Lançamentos Financeiros'
        ordering = ['-criado_em']
 
    @property
    def valor_liquido(self):
        return self.valor - self.desconto
 
    def __str__(self):
        return f"[{self.get_tipo_display()}] {self.descricao} — R$ {self.valor_liquido} ({self.get_status_display()})"
 
 
# ─────────────────────────────────────────
# ESTOQUE
# ─────────────────────────────────────────
 
class Estoque(models.Model):
    class Categoria(models.TextChoices):
        ANESTESICO  = 'anestesico',  'Anestésico'
        INSTRUMENTAL = 'instrumental', 'Instrumental'
        RESINA       = 'resina',      'Resina'
        CIMENTO      = 'cimento',     'Cimento'
        DESCARTAVEL  = 'descartavel', 'Descartável'
        RADIOGRAFIA  = 'radiografia', 'Radiografia'
        HIGIENE      = 'higiene',     'Higiene'
        MEDICAMENTO  = 'medicamento', 'Medicamento'
        OUTRO        = 'outro',       'Outro'
 
    nome              = models.CharField(max_length=150)
    categoria         = models.CharField(max_length=20, choices=Categoria.choices)
    quantidade        = models.IntegerField(default=0)
    quantidade_minima = models.IntegerField(default=5, verbose_name='Qtd. Mínima (alerta)')
    unidade           = models.CharField(max_length=20, help_text='Ex: unidade, caixa, frasco, ml')
    fornecedor        = models.CharField(max_length=150, blank=True, null=True)
    validade          = models.DateField(blank=True, null=True)
    custo_unitario    = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    localizacao       = models.CharField(max_length=100, blank=True, null=True, help_text='Ex: Gaveta 3, Armário A')
    criado_em         = models.DateTimeField(auto_now_add=True)
    atualizado_em     = models.DateTimeField(auto_now=True)
 
    class Meta:
        verbose_name = 'Item de Estoque'
        verbose_name_plural = 'Estoque'
        ordering = ['categoria', 'nome']
 
    @property
    def estoque_baixo(self):
        return self.quantidade <= self.quantidade_minima
 
    def __str__(self):
        alerta = ' ⚠️' if self.estoque_baixo else ''
        return f"{self.nome} — {self.quantidade} {self.unidade}{alerta}"