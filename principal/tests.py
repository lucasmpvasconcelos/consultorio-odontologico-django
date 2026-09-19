"""
tests.py — Suíte de Testes Completa — Sistema de Gestão Odontológica
Cobre: models, serializers, views (CRUD + actions extras), autenticação JWT e dashboard.
"""

from datetime import date, timedelta
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from .models import (
    Usuario, Paciente, Dentista, Consulta,
    Prontuario, Procedimento, ProntuarioProcedimento,
    Financeiro, Estoque,
)


# ═══════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════

def get_tokens_for_user(user):
    """Retorna access token JWT para o usuário."""
    refresh = RefreshToken.for_user(user)
    return str(refresh.access_token)


def make_usuario(username='testuser', perfil='admin', password='Senha@Forte123'):
    user = Usuario.objects.create_user(
        username=username,
        password=password,
        first_name='Test',
        last_name='User',
        email=f'{username}@test.com',
        perfil=perfil,
    )
    return user


def make_paciente(**kwargs):
    defaults = dict(
        nome_completo='João da Silva',
        cpf='529.982.247-25',
        data_nascimento=date(1990, 5, 15),
        telefone='(11) 99999-0001',
        email='joao@test.com',
    )
    defaults.update(kwargs)
    return Paciente.objects.create(**defaults)


def make_dentista(**kwargs):
    defaults = dict(
        nome_completo='Dr. Carlos Souza',
        cro='SP-12345',
        especialidade='Clínico Geral',
        telefone='(11) 3333-4444',
    )
    defaults.update(kwargs)
    return Dentista.objects.create(**defaults)


def make_consulta(paciente, dentista, **kwargs):
    defaults = dict(
        data_hora=timezone.now() + timedelta(days=1),
        duracao_min=60,
        status='agendada',
        tipo='consulta',
    )
    defaults.update(kwargs)
    return Consulta.objects.create(paciente=paciente, dentista=dentista, **defaults)


def make_procedimento(**kwargs):
    defaults = dict(
        nome='Limpeza Dental',
        categoria='preventivo',
        valor_padrao=Decimal('150.00'),
        duracao_media=60,
    )
    defaults.update(kwargs)
    return Procedimento.objects.create(**defaults)


def make_financeiro(paciente=None, **kwargs):
    defaults = dict(
        tipo='receita',
        descricao='Consulta de limpeza',
        valor=Decimal('200.00'),
        desconto=Decimal('0.00'),
        status='pendente',
        forma_pagamento='pix',
    )
    defaults.update(kwargs)
    return Financeiro.objects.create(paciente=paciente, **defaults)


def make_estoque(**kwargs):
    defaults = dict(
        nome='Luva de Látex',
        categoria='descartavel',
        quantidade=100,
        quantidade_minima=10,
        unidade='caixa',
    )
    defaults.update(kwargs)
    return Estoque.objects.create(**defaults)


# ═══════════════════════════════════════════════════════════════════
# TESTES DE MODELS
# ═══════════════════════════════════════════════════════════════════

class PacienteModelTest(TestCase):

    def setUp(self):
        self.paciente = make_paciente(data_nascimento=date(1990, 1, 1))

    def test_str_retorna_nome(self):
        self.assertEqual(str(self.paciente), 'João da Silva')

    def test_idade_calculada_corretamente(self):
        hoje = date.today()
        esperado = hoje.year - 1990 - (
            (hoje.month, hoje.day) < (1, 1)
        )
        self.assertEqual(self.paciente.idade, esperado)

    def test_idade_antes_aniversario(self):
        """Paciente que ainda não fez aniversário este ano."""
        ano_atual = date.today().year
        p = make_paciente(
            cpf='111.444.777-35',
            data_nascimento=date(2000, 12, 31),
        )
        esperado = ano_atual - 2000 - 1
        self.assertEqual(p.idade, esperado)


class DentistaModelTest(TestCase):

    def test_str_retorna_nome_e_especialidade(self):
        d = make_dentista()
        self.assertIn('Dr(a). Dr. Carlos Souza', str(d))
        self.assertIn('Clínico Geral', str(d))


class ProcedimentoModelTest(TestCase):

    def test_str_retorna_nome_e_valor(self):
        p = make_procedimento()
        self.assertIn('Limpeza Dental', str(p))
        self.assertIn('150.00', str(p))


class ConsultaModelTest(TestCase):

    def setUp(self):
        self.paciente = make_paciente()
        self.dentista = make_dentista()

    def test_str_retorna_paciente_data_status(self):
        c = make_consulta(self.paciente, self.dentista)
        s = str(c)
        self.assertIn('João da Silva', s)
        self.assertIn('Agendada', s)


class FinanceiroModelTest(TestCase):

    def test_valor_liquido(self):
        f = make_financeiro(valor=Decimal('500.00'), desconto=Decimal('50.00'))
        self.assertEqual(f.valor_liquido, Decimal('450.00'))

    def test_valor_liquido_sem_desconto(self):
        f = make_financeiro(valor=Decimal('300.00'))
        self.assertEqual(f.valor_liquido, Decimal('300.00'))

    def test_str_contem_descricao_e_status(self):
        f = make_financeiro()
        self.assertIn('Consulta de limpeza', str(f))
        self.assertIn('Pendente', str(f))


class EstoqueModelTest(TestCase):

    def test_estoque_baixo_true_quando_abaixo_do_minimo(self):
        e = make_estoque(quantidade=5, quantidade_minima=10)
        self.assertTrue(e.estoque_baixo)

    def test_estoque_baixo_true_quando_igual_ao_minimo(self):
        e = make_estoque(quantidade=10, quantidade_minima=10)
        self.assertTrue(e.estoque_baixo)

    def test_estoque_baixo_false_quando_acima_do_minimo(self):
        e = make_estoque(quantidade=20, quantidade_minima=10)
        self.assertFalse(e.estoque_baixo)

    def test_str_contem_alerta_quando_estoque_baixo(self):
        e = make_estoque(quantidade=3, quantidade_minima=10)
        self.assertIn('⚠️', str(e))

    def test_str_sem_alerta_quando_estoque_ok(self):
        e = make_estoque(quantidade=50, quantidade_minima=10)
        self.assertNotIn('⚠️', str(e))


class UsuarioModelTest(TestCase):

    def test_str_retorna_nome_e_perfil(self):
        u = make_usuario()
        s = str(u)
        self.assertIn('Test User', s)
        self.assertIn('Administrador', s)


# ═══════════════════════════════════════════════════════════════════
# BASE PARA TESTES DE API
# ═══════════════════════════════════════════════════════════════════

class AuthenticatedAPITestCase(APITestCase):
    """Base com autenticação JWT já configurada."""

    def setUp(self):
        self.user = make_usuario()
        token = get_tokens_for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')


# ═══════════════════════════════════════════════════════════════════
# TESTES DE SERIALIZERS
# ═══════════════════════════════════════════════════════════════════

class UsuarioSerializerTest(TestCase):

    def test_criar_usuario_senhas_iguais(self):
        from .serializers import UsuarioCreateSerializer
        data = {
            'username': 'novo_user',
            'email': 'novo@test.com',
            'first_name': 'Novo',
            'last_name': 'User',
            'perfil': 'recepcionista',
            'password': 'Senha@Forte123',
            'password2': 'Senha@Forte123',
        }
        s = UsuarioCreateSerializer(data=data)
        self.assertTrue(s.is_valid(), s.errors)
        user = s.save()
        self.assertTrue(user.check_password('Senha@Forte123'))

    def test_criar_usuario_senhas_diferentes(self):
        from .serializers import UsuarioCreateSerializer
        data = {
            'username': 'outro_user',
            'password': 'Senha@Forte123',
            'password2': 'SenhaDiferente',
            'perfil': 'recepcionista',
        }
        s = UsuarioCreateSerializer(data=data)
        self.assertFalse(s.is_valid())
        self.assertIn('password2', s.errors)


class PacienteSerializerTest(TestCase):

    def test_cpf_valido_formatado(self):
        """Verifica que CPF já formatado é aceito e que validate_cpf normaliza corretamente."""
        from .serializers import PacienteDetailSerializer
        # Envia CPF já formatado (modelo exige formato xxx.xxx.xxx-xx via RegexValidator)
        data = {
            'nome_completo': 'Maria Souza',
            'cpf': '529.982.247-25',
            'data_nascimento': '1985-03-20',
            'telefone': '(11) 98888-7777',
        }
        s = PacienteDetailSerializer(data=data)
        self.assertTrue(s.is_valid(), s.errors)
        self.assertEqual(s.validated_data['cpf'], '529.982.247-25')

    def test_cpf_sem_formatacao_aceito_e_normalizado(self):
        """O validate_cpf aceita CPF sem formatação e retorna formatado."""
        from .serializers import PacienteDetailSerializer
        s = PacienteDetailSerializer()
        resultado = s.validate_cpf('52998224725')
        self.assertEqual(resultado, '529.982.247-25')

    def test_cpf_invalido_rejeitado(self):
        from .serializers import PacienteDetailSerializer
        data = {
            'nome_completo': 'Maria Souza',
            'cpf': '111.111.111-11',
            'data_nascimento': '1985-03-20',
            'telefone': '(11) 98888-7777',
        }
        s = PacienteDetailSerializer(data=data)
        self.assertFalse(s.is_valid())
        self.assertIn('cpf', s.errors)

    def test_cpf_com_onze_digitos_iguais_invalido(self):
        from .serializers import PacienteDetailSerializer
        data = {
            'nome_completo': 'Maria Souza',
            'cpf': '000.000.000-00',
            'data_nascimento': '1985-03-20',
            'telefone': '(11) 98888-7777',
        }
        s = PacienteDetailSerializer(data=data)
        self.assertFalse(s.is_valid())
        self.assertIn('cpf', s.errors)

    def test_data_nascimento_futura_rejeitada(self):
        from .serializers import PacienteDetailSerializer
        data = {
            'nome_completo': 'Test',
            'cpf': '529.982.247-25',
            'data_nascimento': str(date.today() + timedelta(days=1)),
            'telefone': '(11) 99999-0000',
        }
        s = PacienteDetailSerializer(data=data)
        self.assertFalse(s.is_valid())
        self.assertIn('data_nascimento', s.errors)

    def test_data_nascimento_antes_1900_rejeitada(self):
        from .serializers import PacienteDetailSerializer
        data = {
            'nome_completo': 'Test',
            'cpf': '529.982.247-25',
            'data_nascimento': '1899-12-31',
            'telefone': '(11) 99999-0000',
        }
        s = PacienteDetailSerializer(data=data)
        self.assertFalse(s.is_valid())
        self.assertIn('data_nascimento', s.errors)


class DentistaSerializerTest(TestCase):

    def test_cro_valido(self):
        from .serializers import DentistaSerializer
        data = {
            'nome_completo': 'Dra. Ana Lima',
            'cro': 'sp-98765',  # minúsculo — deve ser normalizado
            'especialidade': 'Ortodontia',
            'telefone': '(11) 2222-3333',
        }
        s = DentistaSerializer(data=data)
        self.assertTrue(s.is_valid(), s.errors)
        self.assertEqual(s.validated_data['cro'], 'SP-98765')

    def test_cro_invalido_sem_uf(self):
        from .serializers import DentistaSerializer
        data = {
            'nome_completo': 'Dra. Ana Lima',
            'cro': '12345',
            'especialidade': 'Ortodontia',
            'telefone': '(11) 2222-3333',
        }
        s = DentistaSerializer(data=data)
        self.assertFalse(s.is_valid())
        self.assertIn('cro', s.errors)

    def test_cro_invalido_formato_errado(self):
        from .serializers import DentistaSerializer
        data = {
            'nome_completo': 'Dra. Ana Lima',
            'cro': 'S-1234',  # UF incompleto
            'especialidade': 'Ortodontia',
            'telefone': '(11) 2222-3333',
        }
        s = DentistaSerializer(data=data)
        self.assertFalse(s.is_valid())
        self.assertIn('cro', s.errors)


class ConsultaSerializerTest(TestCase):

    def setUp(self):
        self.paciente = make_paciente()
        self.dentista = make_dentista()

    def test_conflito_de_agenda_rejeitado(self):
        from .serializers import ConsultaSerializer
        # Cria consulta existente: amanhã das 10h às 11h
        data_hora_existente = timezone.now().replace(
            hour=10, minute=0, second=0, microsecond=0
        ) + timedelta(days=2)
        make_consulta(self.paciente, self.dentista, data_hora=data_hora_existente, duracao_min=60)

        # Tenta criar nova consulta que se sobrepõe: 10h30 às 11h30
        data = {
            'paciente': self.paciente.pk,
            'dentista': self.dentista.pk,
            'data_hora': (data_hora_existente + timedelta(minutes=30)).isoformat(),
            'duracao_min': 60,
            'status': 'agendada',
            'tipo': 'consulta',
        }
        s = ConsultaSerializer(data=data)
        self.assertFalse(s.is_valid())
        self.assertIn('data_hora', s.errors)

    def test_sem_conflito_de_agenda_aceito(self):
        from .serializers import ConsultaSerializer
        # Cria consulta existente: amanhã às 10h (60 min)
        data_hora_existente = timezone.now().replace(
            hour=10, minute=0, second=0, microsecond=0
        ) + timedelta(days=3)
        make_consulta(self.paciente, self.dentista, data_hora=data_hora_existente, duracao_min=60)

        # Cria nova consulta logo após: às 11h
        data = {
            'paciente': self.paciente.pk,
            'dentista': self.dentista.pk,
            'data_hora': (data_hora_existente + timedelta(hours=1)).isoformat(),
            'duracao_min': 60,
            'status': 'agendada',
            'tipo': 'consulta',
        }
        s = ConsultaSerializer(data=data)
        self.assertTrue(s.is_valid(), s.errors)


class FinanceiroSerializerTest(TestCase):

    def test_desconto_maior_que_valor_rejeitado(self):
        from .serializers import FinanceiroSerializer
        data = {
            'tipo': 'receita',
            'descricao': 'Consulta',
            'valor': '100.00',
            'desconto': '150.00',
            'forma_pagamento': 'dinheiro',
        }
        s = FinanceiroSerializer(data=data)
        self.assertFalse(s.is_valid())
        self.assertIn('desconto', s.errors)

    def test_desconto_negativo_rejeitado(self):
        from .serializers import FinanceiroSerializer
        data = {
            'tipo': 'receita',
            'descricao': 'Consulta',
            'valor': '100.00',
            'desconto': '-10.00',
            'forma_pagamento': 'dinheiro',
        }
        s = FinanceiroSerializer(data=data)
        self.assertFalse(s.is_valid())
        self.assertIn('desconto', s.errors)

    def test_valor_negativo_rejeitado(self):
        from .serializers import FinanceiroSerializer
        data = {
            'tipo': 'receita',
            'descricao': 'Consulta',
            'valor': '-50.00',
            'desconto': '0.00',
            'forma_pagamento': 'dinheiro',
        }
        s = FinanceiroSerializer(data=data)
        self.assertFalse(s.is_valid())
        self.assertIn('valor', s.errors)

    def test_parcelas_zero_rejeitado(self):
        from .serializers import FinanceiroSerializer
        data = {
            'tipo': 'receita',
            'descricao': 'Consulta',
            'valor': '100.00',
            'desconto': '0.00',
            'forma_pagamento': 'dinheiro',
            'parcelas': 0,
        }
        s = FinanceiroSerializer(data=data)
        self.assertFalse(s.is_valid())
        self.assertIn('parcelas', s.errors)

    def test_dados_validos_aceitos(self):
        from .serializers import FinanceiroSerializer
        data = {
            'tipo': 'receita',
            'descricao': 'Consulta',
            'valor': '200.00',
            'desconto': '20.00',
            'forma_pagamento': 'pix',
            'parcelas': 1,
        }
        s = FinanceiroSerializer(data=data)
        self.assertTrue(s.is_valid(), s.errors)


class EstoqueSerializerTest(TestCase):

    def test_quantidade_negativa_rejeitada(self):
        from .serializers import EstoqueSerializer
        data = {
            'nome': 'Agulha',
            'categoria': 'descartavel',
            'quantidade': -1,
            'quantidade_minima': 5,
            'unidade': 'unidade',
        }
        s = EstoqueSerializer(data=data)
        self.assertFalse(s.is_valid())
        self.assertIn('quantidade', s.errors)

    def test_quantidade_zero_aceita(self):
        from .serializers import EstoqueSerializer
        data = {
            'nome': 'Agulha',
            'categoria': 'descartavel',
            'quantidade': 0,
            'quantidade_minima': 5,
            'unidade': 'unidade',
        }
        s = EstoqueSerializer(data=data)
        self.assertTrue(s.is_valid(), s.errors)


class ProntuarioProcedimentoSerializerTest(TestCase):

    def setUp(self):
        self.paciente   = make_paciente()
        self.dentista   = make_dentista()
        self.procedimento = make_procedimento()
        self.prontuario = Prontuario.objects.create(
            paciente=self.paciente,
            dentista=self.dentista,
            data_atendimento=date.today(),
            anamnese='Sem queixas.',
            diagnostico='Saudável.',
        )

    def test_duplicata_com_dente_none_rejeitada(self):
        from .serializers import ProntuarioProcedimentoSerializer
        # Cria o primeiro
        ProntuarioProcedimento.objects.create(
            prontuario=self.prontuario,
            procedimento=self.procedimento,
            quantidade=1,
            valor_cobrado=Decimal('150.00'),
            dente=None,
        )
        # Tenta criar o segundo com dente=None no mesmo prontuário/procedimento
        data = {
            'prontuario': self.prontuario.pk,
            'procedimento': self.procedimento.pk,
            'quantidade': 1,
            'valor_cobrado': '150.00',
            'dente': None,
        }
        s = ProntuarioProcedimentoSerializer(data=data)
        self.assertFalse(s.is_valid())

    def test_mesmo_procedimento_dentes_diferentes_aceito(self):
        from .serializers import ProntuarioProcedimentoSerializer
        ProntuarioProcedimento.objects.create(
            prontuario=self.prontuario,
            procedimento=self.procedimento,
            quantidade=1,
            valor_cobrado=Decimal('150.00'),
            dente='11',
        )
        data = {
            'prontuario': self.prontuario.pk,
            'procedimento': self.procedimento.pk,
            'quantidade': 1,
            'valor_cobrado': '150.00',
            'dente': '21',  # dente diferente → OK
        }
        s = ProntuarioProcedimentoSerializer(data=data)
        self.assertTrue(s.is_valid(), s.errors)


class ProcedimentoSerializerTest(TestCase):

    def test_valor_negativo_rejeitado(self):
        from .serializers import ProcedimentoSerializer
        data = {
            'nome': 'Extração',
            'categoria': 'cirurgia',
            'valor_padrao': '-10.00',
            'duracao_media': 45,
        }
        s = ProcedimentoSerializer(data=data)
        self.assertFalse(s.is_valid())
        self.assertIn('valor_padrao', s.errors)

    def test_duracao_zero_rejeitada(self):
        from .serializers import ProcedimentoSerializer
        data = {
            'nome': 'Extração',
            'categoria': 'cirurgia',
            'valor_padrao': '300.00',
            'duracao_media': 0,
        }
        s = ProcedimentoSerializer(data=data)
        self.assertFalse(s.is_valid())
        self.assertIn('duracao_media', s.errors)


# ═══════════════════════════════════════════════════════════════════
# TESTES DE AUTENTICAÇÃO JWT
# ═══════════════════════════════════════════════════════════════════

class JWTAuthTest(APITestCase):

    def setUp(self):
        self.user = make_usuario(username='jwtuser', password='Senha@Forte123')
        self.url_token = reverse('token_obtain_pair')

    def test_login_valido_retorna_tokens(self):
        resp = self.client.post(self.url_token, {
            'username': 'jwtuser',
            'password': 'Senha@Forte123',
        })
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('access', resp.data)
        self.assertIn('refresh', resp.data)

    def test_login_senha_errada_retorna_401(self):
        resp = self.client.post(self.url_token, {
            'username': 'jwtuser',
            'password': 'SenhaErrada',
        })
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_acesso_sem_token_retorna_401(self):
        resp = self.client.get(reverse('paciente-list'))
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_acesso_com_token_valido(self):
        token = get_tokens_for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        resp = self.client.get(reverse('paciente-list'))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)


# ═══════════════════════════════════════════════════════════════════
# TESTES DO DASHBOARD
# ═══════════════════════════════════════════════════════════════════

class DashboardViewTest(AuthenticatedAPITestCase):

    def test_dashboard_retorna_200(self):
        resp = self.client.get(reverse('dashboard'))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_dashboard_contem_todas_chaves(self):
        resp = self.client.get(reverse('dashboard'))
        data = resp.data
        self.assertIn('consultas', data)
        self.assertIn('financeiro', data)
        self.assertIn('estoque', data)
        self.assertIn('pacientes', data)
        self.assertIn('dentistas', data)
        self.assertIn('data_referencia', data)

    def test_dashboard_consultas_hoje(self):
        paciente = make_paciente()
        dentista = make_dentista()
        # Cria uma consulta para hoje
        make_consulta(paciente, dentista, data_hora=timezone.now())
        resp = self.client.get(reverse('dashboard'))
        self.assertGreaterEqual(resp.data['consultas']['hoje_total'], 1)

    def test_dashboard_sem_autenticacao_retorna_401(self):
        self.client.credentials()  # remove token
        resp = self.client.get(reverse('dashboard'))
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


# ═══════════════════════════════════════════════════════════════════
# TESTES DE USUÁRIO
# ═══════════════════════════════════════════════════════════════════

class UsuarioViewSetTest(AuthenticatedAPITestCase):

    def test_listar_usuarios(self):
        resp = self.client.get(reverse('usuario-list'))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_endpoint_me_retorna_usuario_logado(self):
        resp = self.client.get(reverse('usuario-me'))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['username'], self.user.username)

    def test_criar_usuario_valido(self):
        data = {
            'username': 'novo_dentista',
            'email': 'dent@test.com',
            'first_name': 'Novo',
            'last_name': 'Dentista',
            'perfil': 'dentista',
            'password': 'Senha@Forte456',
            'password2': 'Senha@Forte456',
        }
        resp = self.client.post(reverse('usuario-list'), data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Usuario.objects.filter(username='novo_dentista').count(), 1)

    def test_criar_usuario_senha_fraca_rejeitado(self):
        data = {
            'username': 'user_fraco',
            'perfil': 'recepcionista',
            'password': '123',
            'password2': '123',
        }
        resp = self.client.post(reverse('usuario-list'), data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_detalhe_usuario(self):
        resp = self.client.get(reverse('usuario-detail', args=[self.user.pk]))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['id'], self.user.pk)

    def test_atualizar_usuario(self):
        resp = self.client.patch(
            reverse('usuario-detail', args=[self.user.pk]),
            {'first_name': 'Atualizado'},
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['first_name'], 'Atualizado')

    def test_deletar_usuario(self):
        u = make_usuario(username='deletar_user')
        resp = self.client.delete(reverse('usuario-detail', args=[u.pk]))
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Usuario.objects.filter(pk=u.pk).exists())


# ═══════════════════════════════════════════════════════════════════
# TESTES DE PACIENTE
# ═══════════════════════════════════════════════════════════════════

class PacienteViewSetTest(AuthenticatedAPITestCase):

    def setUp(self):
        super().setUp()
        self.paciente = make_paciente()

    def test_listar_pacientes(self):
        resp = self.client.get(reverse('paciente-list'))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(resp.data['count'], 1)

    def test_criar_paciente_valido(self):
        data = {
            'nome_completo': 'Maria Teste',
            'cpf': '111.444.777-35',
            'data_nascimento': '1985-06-10',
            'telefone': '(11) 97777-6666',
        }
        resp = self.client.post(reverse('paciente-list'), data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_criar_paciente_cpf_invalido(self):
        data = {
            'nome_completo': 'Erro CPF',
            'cpf': '000.000.000-00',
            'data_nascimento': '1990-01-01',
            'telefone': '(11) 99999-9999',
        }
        resp = self.client.post(reverse('paciente-list'), data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_detalhe_paciente(self):
        resp = self.client.get(reverse('paciente-detail', args=[self.paciente.pk]))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['nome_completo'], 'João da Silva')

    def test_atualizar_paciente(self):
        resp = self.client.patch(
            reverse('paciente-detail', args=[self.paciente.pk]),
            {'email': 'novo@email.com'},
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['email'], 'novo@email.com')

    def test_deletar_paciente_sem_consultas(self):
        p = make_paciente(cpf='111.444.777-35', nome_completo='Para Deletar')
        resp = self.client.delete(reverse('paciente-detail', args=[p.pk]))
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

    def test_deletar_paciente_com_consultas_bloqueado(self):
        dentista = make_dentista()
        make_consulta(self.paciente, dentista)
        resp = self.client.delete(reverse('paciente-detail', args=[self.paciente.pk]))
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('detail', resp.data)

    def test_buscar_paciente_por_nome(self):
        resp = self.client.get(reverse('paciente-buscar') + '?q=João')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(resp.data), 1)

    def test_buscar_sem_parametro_retorna_400(self):
        resp = self.client.get(reverse('paciente-buscar'))
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_consultas_do_paciente(self):
        dentista = make_dentista()
        make_consulta(self.paciente, dentista)
        resp = self.client.get(reverse('paciente-consultas', args=[self.paciente.pk]))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(resp.data), 1)

    def test_prontuarios_do_paciente(self):
        dentista = make_dentista()
        Prontuario.objects.create(
            paciente=self.paciente,
            dentista=dentista,
            data_atendimento=date.today(),
            anamnese='Sem queixas.',
            diagnostico='Saudável.',
        )
        resp = self.client.get(reverse('paciente-prontuarios', args=[self.paciente.pk]))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(resp.data), 1)

    def test_financeiro_do_paciente(self):
        make_financeiro(paciente=self.paciente)
        resp = self.client.get(reverse('paciente-financeiro', args=[self.paciente.pk]))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(resp.data), 1)

    def test_filtro_por_nome(self):
        resp = self.client.get(reverse('paciente-list') + '?nome=João')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        for p in resp.data['results']:
            self.assertIn('João', p['nome_completo'])


# ═══════════════════════════════════════════════════════════════════
# TESTES DE DENTISTA
# ═══════════════════════════════════════════════════════════════════

class DentistaViewSetTest(AuthenticatedAPITestCase):

    def setUp(self):
        super().setUp()
        self.dentista = make_dentista()

    def test_listar_dentistas(self):
        resp = self.client.get(reverse('dentista-list'))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_criar_dentista_valido(self):
        data = {
            'nome_completo': 'Dra. Patrícia Lima',
            'cro': 'RJ-54321',
            'especialidade': 'Pediatria',
            'telefone': '(21) 5555-6666',
        }
        resp = self.client.post(reverse('dentista-list'), data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_criar_dentista_cro_invalido(self):
        data = {
            'nome_completo': 'Dr. Inválido',
            'cro': 'CRO-123',
            'especialidade': 'Clínico',
            'telefone': '(11) 0000-0000',
        }
        resp = self.client.post(reverse('dentista-list'), data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_detalhe_dentista(self):
        resp = self.client.get(reverse('dentista-detail', args=[self.dentista.pk]))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_atualizar_dentista(self):
        resp = self.client.patch(
            reverse('dentista-detail', args=[self.dentista.pk]),
            {'especialidade': 'Implantodontia'},
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['especialidade'], 'Implantodontia')

    def test_deletar_dentista(self):
        d = make_dentista(cro='MG-99999', nome_completo='Para Deletar')
        resp = self.client.delete(reverse('dentista-detail', args=[d.pk]))
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

    def test_agenda_do_dentista_hoje(self):
        resp = self.client.get(reverse('dentista-agenda', args=[self.dentista.pk]))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('consultas', resp.data)
        self.assertIn('total', resp.data)

    def test_agenda_data_invalida(self):
        resp = self.client.get(
            reverse('dentista-agenda', args=[self.dentista.pk]) + '?data=invalido'
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_agenda_com_data_especifica(self):
        paciente = make_paciente()
        data_consulta = date.today() + timedelta(days=5)
        make_consulta(
            paciente, self.dentista,
            data_hora=timezone.make_aware(
                timezone.datetime.combine(data_consulta, timezone.datetime.min.time().replace(hour=14))
            )
        )
        resp = self.client.get(
            reverse('dentista-agenda', args=[self.dentista.pk]) + f'?data={data_consulta.isoformat()}'
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['total'], 1)


# ═══════════════════════════════════════════════════════════════════
# TESTES DE CONSULTA
# ═══════════════════════════════════════════════════════════════════

class ConsultaViewSetTest(AuthenticatedAPITestCase):

    def setUp(self):
        super().setUp()
        self.paciente = make_paciente()
        self.dentista = make_dentista()
        self.consulta = make_consulta(self.paciente, self.dentista)

    def test_listar_consultas(self):
        resp = self.client.get(reverse('consulta-list'))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_criar_consulta_valida(self):
        data_hora = (timezone.now() + timedelta(days=10)).replace(
            hour=9, minute=0, second=0, microsecond=0
        )
        data = {
            'paciente': self.paciente.pk,
            'dentista': self.dentista.pk,
            'data_hora': data_hora.isoformat(),
            'duracao_min': 60,
            'status': 'agendada',
            'tipo': 'consulta',
        }
        resp = self.client.post(reverse('consulta-list'), data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_detalhe_consulta(self):
        resp = self.client.get(reverse('consulta-detail', args=[self.consulta.pk]))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_confirmar_consulta_agendada(self):
        resp = self.client.patch(reverse('consulta-confirmar', args=[self.consulta.pk]))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['status'], 'confirmada')
        self.assertTrue(resp.data['confirmada'])

    def test_confirmar_consulta_realizada_rejeitado(self):
        self.consulta.status = 'realizada'
        self.consulta.save()
        resp = self.client.patch(reverse('consulta-confirmar', args=[self.consulta.pk]))
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cancelar_consulta_agendada(self):
        resp = self.client.patch(reverse('consulta-cancelar', args=[self.consulta.pk]))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['status'], 'cancelada')

    def test_cancelar_consulta_realizada_rejeitado(self):
        self.consulta.status = 'realizada'
        self.consulta.save()
        resp = self.client.patch(reverse('consulta-cancelar', args=[self.consulta.pk]))
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cancelar_consulta_ja_cancelada_rejeitado(self):
        self.consulta.status = 'cancelada'
        self.consulta.save()
        resp = self.client.patch(reverse('consulta-cancelar', args=[self.consulta.pk]))
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_realizar_consulta(self):
        resp = self.client.patch(reverse('consulta-realizar', args=[self.consulta.pk]))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['status'], 'realizada')

    def test_realizar_consulta_cancelada_rejeitado(self):
        self.consulta.status = 'cancelada'
        self.consulta.save()
        resp = self.client.patch(reverse('consulta-realizar', args=[self.consulta.pk]))
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_endpoint_hoje(self):
        resp = self.client.get(reverse('consulta-hoje'))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('consultas', resp.data)
        self.assertIn('total', resp.data)

    def test_reagendar_consulta_cancelada(self):
        self.consulta.status = 'cancelada'
        self.consulta.save()
        nova_data = (timezone.now() + timedelta(days=15)).replace(
            hour=14, minute=0, second=0, microsecond=0
        )
        resp = self.client.patch(
            reverse('consulta-reagendar', args=[self.consulta.pk]),
            {'data_hora': nova_data.isoformat()},
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['status'], 'agendada')

    def test_reagendar_consulta_falta(self):
        self.consulta.status = 'falta'
        self.consulta.save()
        nova_data = (timezone.now() + timedelta(days=20)).replace(
            hour=10, minute=0, second=0, microsecond=0
        )
        resp = self.client.patch(
            reverse('consulta-reagendar', args=[self.consulta.pk]),
            {'data_hora': nova_data.isoformat()},
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['status'], 'agendada')

    def test_reagendar_consulta_agendada_rejeitado(self):
        resp = self.client.patch(
            reverse('consulta-reagendar', args=[self.consulta.pk]),
            {'data_hora': (timezone.now() + timedelta(days=5)).isoformat()},
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reagendar_sem_data_hora_retorna_400(self):
        self.consulta.status = 'cancelada'
        self.consulta.save()
        resp = self.client.patch(
            reverse('consulta-reagendar', args=[self.consulta.pk]),
            {},
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_filtro_por_status(self):
        resp = self.client.get(reverse('consulta-list') + '?status=agendada')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        for c in resp.data['results']:
            self.assertEqual(c['status'], 'agendada')

    def test_deletar_consulta(self):
        resp = self.client.delete(reverse('consulta-detail', args=[self.consulta.pk]))
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)


# ═══════════════════════════════════════════════════════════════════
# TESTES DE PRONTUÁRIO
# ═══════════════════════════════════════════════════════════════════

class ProntuarioViewSetTest(AuthenticatedAPITestCase):

    def setUp(self):
        super().setUp()
        self.paciente   = make_paciente()
        self.dentista   = make_dentista()
        self.prontuario = Prontuario.objects.create(
            paciente=self.paciente,
            dentista=self.dentista,
            data_atendimento=date.today(),
            anamnese='Sem alergias.',
            diagnostico='Cárie no dente 36.',
        )

    def test_listar_prontuarios(self):
        resp = self.client.get(reverse('prontuario-list'))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(resp.data['count'], 1)

    def test_criar_prontuario_valido(self):
        data = {
            'paciente': self.paciente.pk,
            'dentista': self.dentista.pk,
            'data_atendimento': str(date.today()),
            'anamnese': 'Paciente relata dor.',
            'diagnostico': 'Pulpite.',
        }
        resp = self.client.post(reverse('prontuario-list'), data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_criar_prontuario_data_futura_rejeitado(self):
        data = {
            'paciente': self.paciente.pk,
            'dentista': self.dentista.pk,
            'data_atendimento': str(date.today() + timedelta(days=1)),
            'anamnese': 'Teste.',
            'diagnostico': 'Teste.',
        }
        resp = self.client.post(reverse('prontuario-list'), data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_detalhe_prontuario(self):
        resp = self.client.get(reverse('prontuario-detail', args=[self.prontuario.pk]))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('procedimentos_detail', resp.data)

    def test_atualizar_prontuario(self):
        resp = self.client.patch(
            reverse('prontuario-detail', args=[self.prontuario.pk]),
            {'diagnostico': 'Diagnóstico atualizado.'},
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['diagnostico'], 'Diagnóstico atualizado.')

    def test_filtro_por_paciente(self):
        resp = self.client.get(
            reverse('prontuario-list') + f'?paciente_id={self.paciente.pk}'
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        for p in resp.data['results']:
            self.assertEqual(p['paciente'], self.paciente.pk)

    def test_filtro_por_dentista(self):
        resp = self.client.get(
            reverse('prontuario-list') + f'?dentista_id={self.dentista.pk}'
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_deletar_prontuario(self):
        resp = self.client.delete(reverse('prontuario-detail', args=[self.prontuario.pk]))
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)


# ═══════════════════════════════════════════════════════════════════
# TESTES DE PROCEDIMENTO
# ═══════════════════════════════════════════════════════════════════

class ProcedimentoViewSetTest(AuthenticatedAPITestCase):

    def setUp(self):
        super().setUp()
        self.procedimento = make_procedimento()

    def test_listar_procedimentos(self):
        resp = self.client.get(reverse('procedimento-list'))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_criar_procedimento_valido(self):
        data = {
            'nome': 'Extração Simples',
            'categoria': 'cirurgia',
            'valor_padrao': '250.00',
            'duracao_media': 45,
        }
        resp = self.client.post(reverse('procedimento-list'), data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_criar_procedimento_valor_negativo(self):
        data = {
            'nome': 'Procedimento Inválido',
            'categoria': 'outro',
            'valor_padrao': '-10.00',
            'duracao_media': 30,
        }
        resp = self.client.post(reverse('procedimento-list'), data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_detalhe_procedimento(self):
        resp = self.client.get(reverse('procedimento-detail', args=[self.procedimento.pk]))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('categoria_display', resp.data)

    def test_atualizar_procedimento(self):
        resp = self.client.patch(
            reverse('procedimento-detail', args=[self.procedimento.pk]),
            {'valor_padrao': '180.00'},
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(str(resp.data['valor_padrao']), '180.00')

    def test_filtro_por_categoria(self):
        resp = self.client.get(reverse('procedimento-list') + '?categoria=preventivo')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_filtro_ativo(self):
        resp = self.client.get(reverse('procedimento-list') + '?ativo=true')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_deletar_procedimento(self):
        p = make_procedimento(nome='Para Deletar', codigo_tuss='99999')
        resp = self.client.delete(reverse('procedimento-detail', args=[p.pk]))
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)


# ═══════════════════════════════════════════════════════════════════
# TESTES FINANCEIRO
# ═══════════════════════════════════════════════════════════════════

class FinanceiroViewSetTest(AuthenticatedAPITestCase):

    def setUp(self):
        super().setUp()
        self.paciente   = make_paciente()
        self.lancamento = make_financeiro(paciente=self.paciente)

    def test_listar_lancamentos(self):
        resp = self.client.get(reverse('financeiro-list'))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_criar_lancamento_valido(self):
        data = {
            'tipo': 'receita',
            'descricao': 'Pagamento de consulta',
            'valor': '350.00',
            'desconto': '0.00',
            'forma_pagamento': 'credito',
            'status': 'pendente',
        }
        resp = self.client.post(reverse('financeiro-list'), data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_criar_lancamento_desconto_maior_que_valor(self):
        data = {
            'tipo': 'receita',
            'descricao': 'Consulta',
            'valor': '100.00',
            'desconto': '200.00',
            'forma_pagamento': 'dinheiro',
        }
        resp = self.client.post(reverse('financeiro-list'), data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_criar_lancamento_desconto_negativo(self):
        data = {
            'tipo': 'receita',
            'descricao': 'Consulta',
            'valor': '100.00',
            'desconto': '-10.00',
            'forma_pagamento': 'dinheiro',
        }
        resp = self.client.post(reverse('financeiro-list'), data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_detalhe_lancamento(self):
        resp = self.client.get(reverse('financeiro-detail', args=[self.lancamento.pk]))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('valor_liquido', resp.data)

    def test_atualizar_lancamento(self):
        resp = self.client.patch(
            reverse('financeiro-detail', args=[self.lancamento.pk]),
            {'status': 'pago'},
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['status'], 'pago')

    def test_resumo_financeiro(self):
        # Garante ao menos um lançamento receita e um despesa
        make_financeiro(tipo='despesa', descricao='Aluguel', valor=Decimal('1000.00'))
        resp = self.client.get(reverse('financeiro-resumo'))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('receitas', resp.data)
        self.assertIn('despesas', resp.data)
        self.assertIn('saldo', resp.data)
        self.assertIn('pendentes', resp.data)

    def test_filtro_por_tipo(self):
        resp = self.client.get(reverse('financeiro-list') + '?tipo=receita')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        for item in resp.data['results']:
            self.assertEqual(item['tipo'], 'receita')

    def test_filtro_por_status(self):
        resp = self.client.get(reverse('financeiro-list') + '?status=pendente')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_deletar_lancamento(self):
        resp = self.client.delete(reverse('financeiro-detail', args=[self.lancamento.pk]))
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)


# ═══════════════════════════════════════════════════════════════════
# TESTES DE ESTOQUE
# ═══════════════════════════════════════════════════════════════════

class EstoqueViewSetTest(AuthenticatedAPITestCase):

    def setUp(self):
        super().setUp()
        self.item = make_estoque()

    def test_listar_estoque(self):
        resp = self.client.get(reverse('estoque-list'))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_criar_item_valido(self):
        data = {
            'nome': 'Anestésico Lidocaína',
            'categoria': 'anestesico',
            'quantidade': 50,
            'quantidade_minima': 10,
            'unidade': 'ampola',
        }
        resp = self.client.post(reverse('estoque-list'), data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_criar_item_quantidade_negativa(self):
        data = {
            'nome': 'Item Inválido',
            'categoria': 'outro',
            'quantidade': -5,
            'quantidade_minima': 2,
            'unidade': 'unidade',
        }
        resp = self.client.post(reverse('estoque-list'), data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_detalhe_item(self):
        resp = self.client.get(reverse('estoque-detail', args=[self.item.pk]))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('estoque_baixo', resp.data)
        self.assertIn('dias_para_vencer', resp.data)

    def test_alertas_estoque_baixo(self):
        make_estoque(nome='Item Crítico', quantidade=1, quantidade_minima=10)
        resp = self.client.get(reverse('estoque-alertas'))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('estoque_baixo', resp.data)
        self.assertIn('vencendo_em_30_dias', resp.data)
        self.assertIn('vencidos', resp.data)
        self.assertGreaterEqual(len(resp.data['estoque_baixo']), 1)

    def test_alertas_item_vencido(self):
        make_estoque(
            nome='Item Vencido',
            validade=date.today() - timedelta(days=5),
        )
        resp = self.client.get(reverse('estoque-alertas'))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(resp.data['vencidos']), 1)

    def test_alertas_item_vencendo(self):
        make_estoque(
            nome='Vence Em Breve',
            validade=date.today() + timedelta(days=15),
        )
        resp = self.client.get(reverse('estoque-alertas'))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(resp.data['vencendo_em_30_dias']), 1)

    def test_ajustar_quantidade_adicionar(self):
        qtd_original = self.item.quantidade
        resp = self.client.patch(
            reverse('estoque-ajustar-quantidade', args=[self.item.pk]),
            {'quantidade': 20, 'operacao': 'adicionar'},
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['quantidade'], qtd_original + 20)

    def test_ajustar_quantidade_remover(self):
        qtd_original = self.item.quantidade
        resp = self.client.patch(
            reverse('estoque-ajustar-quantidade', args=[self.item.pk]),
            {'quantidade': 30, 'operacao': 'remover'},
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['quantidade'], qtd_original - 30)

    def test_ajustar_quantidade_remover_abaixo_de_zero_rejeitado(self):
        resp = self.client.patch(
            reverse('estoque-ajustar-quantidade', args=[self.item.pk]),
            {'quantidade': 9999, 'operacao': 'remover'},
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Quantidade insuficiente', resp.data['detail'])

    def test_ajustar_quantidade_definir(self):
        resp = self.client.patch(
            reverse('estoque-ajustar-quantidade', args=[self.item.pk]),
            {'quantidade': 55, 'operacao': 'definir'},
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['quantidade'], 55)

    def test_ajustar_quantidade_operacao_invalida(self):
        resp = self.client.patch(
            reverse('estoque-ajustar-quantidade', args=[self.item.pk]),
            {'quantidade': 10, 'operacao': 'multiplicar'},
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_ajustar_quantidade_sem_campo_quantidade(self):
        resp = self.client.patch(
            reverse('estoque-ajustar-quantidade', args=[self.item.pk]),
            {'operacao': 'adicionar'},
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_ajustar_quantidade_negativa_rejeitado(self):
        resp = self.client.patch(
            reverse('estoque-ajustar-quantidade', args=[self.item.pk]),
            {'quantidade': -5, 'operacao': 'adicionar'},
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_deletar_item(self):
        resp = self.client.delete(reverse('estoque-detail', args=[self.item.pk]))
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

    def test_filtro_por_categoria(self):
        resp = self.client.get(reverse('estoque-list') + '?categoria=descartavel')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)


# ═══════════════════════════════════════════════════════════════════
# TESTES DE PRONTUÁRIO-PROCEDIMENTO
# ═══════════════════════════════════════════════════════════════════

class ProntuarioProcedimentoViewSetTest(AuthenticatedAPITestCase):

    def setUp(self):
        super().setUp()
        self.paciente     = make_paciente()
        self.dentista     = make_dentista()
        self.procedimento = make_procedimento()
        self.prontuario   = Prontuario.objects.create(
            paciente=self.paciente,
            dentista=self.dentista,
            data_atendimento=date.today(),
            anamnese='Anamnese teste.',
            diagnostico='Diagnóstico teste.',
        )

    def test_criar_prontuario_procedimento_valido(self):
        data = {
            'prontuario': self.prontuario.pk,
            'procedimento': self.procedimento.pk,
            'quantidade': 1,
            'valor_cobrado': '150.00',
            'dente': '36',
        }
        resp = self.client.post(reverse('prontuario-procedimento-list'), data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertIn('procedimento_nome', resp.data)

    def test_listar_prontuario_procedimentos(self):
        ProntuarioProcedimento.objects.create(
            prontuario=self.prontuario,
            procedimento=self.procedimento,
            quantidade=1,
            valor_cobrado=Decimal('150.00'),
            dente='11',
        )
        resp = self.client.get(reverse('prontuario-procedimento-list'))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(resp.data['count'], 1)

    def test_duplicata_rejeitada(self):
        ProntuarioProcedimento.objects.create(
            prontuario=self.prontuario,
            procedimento=self.procedimento,
            quantidade=1,
            valor_cobrado=Decimal('150.00'),
            dente='36',
        )
        data = {
            'prontuario': self.prontuario.pk,
            'procedimento': self.procedimento.pk,
            'quantidade': 1,
            'valor_cobrado': '150.00',
            'dente': '36',
        }
        resp = self.client.post(reverse('prontuario-procedimento-list'), data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_filtro_por_prontuario(self):
        ProntuarioProcedimento.objects.create(
            prontuario=self.prontuario,
            procedimento=self.procedimento,
            quantidade=1,
            valor_cobrado=Decimal('150.00'),
        )
        resp = self.client.get(
            reverse('prontuario-procedimento-list') + f'?prontuario={self.prontuario.pk}'
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(resp.data['count'], 1)
