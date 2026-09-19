# 🦷 Sistema de Gestão Odontológica — API REST

API REST completa para gestão de consultório odontológico, desenvolvida com **Django 6** e **Django REST Framework**.

---

## ✨ Funcionalidades

| Módulo | Descrição |
|--------|-----------|
| 👤 Usuários | Autenticação JWT com perfis (Admin, Dentista, Recepcionista) |
| 🧑‍⚕️ Pacientes | Cadastro completo com CPF validado, histórico e convênio |
| 🦷 Dentistas | Cadastro com CRO, especialidade e agenda semanal |
| 📅 Consultas | Agendamento com validação de conflito e controle de status |
| 📋 Prontuários | Registro clínico com odontograma JSON e radiografias |
| 💊 Procedimentos | Catálogo de procedimentos com categorias e valores |
| 💰 Financeiro | Lançamentos de receitas/despesas com formas de pagamento |
| 📦 Estoque | Controle de materiais com alertas de reposição e vencimento |
| 📊 Dashboard | Métricas em tempo real para a tela inicial |

---

## 🛠️ Tecnologias

- **Python 3.11+**
- **Django 6.0**
- **Django REST Framework 3.17**
- **djangorestframework-simplejwt** — Autenticação JWT
- **drf-spectacular** — Documentação OpenAPI/Swagger
- **django-filter** — Filtros avançados
- **Pillow** — Upload de imagens
- **python-decouple** — Variáveis de ambiente

---

## 🚀 Instalação e Configuração

### 1. Clone o repositório

```bash
git clone <url-do-repositorio>
cd consultorio-odontologico-django
```

### 2. Crie e ative o ambiente virtual

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/macOS
source venv/bin/activate
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Configure as variáveis de ambiente

```bash
cp .env.example .env
# Edite o .env com seus valores
```

Variáveis disponíveis:

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `SECRET_KEY` | insecure-key | Chave secreta Django (obrigatório mudar em produção) |
| `DEBUG` | `True` | Modo debug |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | Hosts permitidos |

### 5. Aplique as migrations

```bash
python manage.py migrate
```

### 6. Crie um superusuário

```bash
python manage.py createsuperuser
```

### 7. Inicie o servidor

```bash
python manage.py runserver
```

---

## 🔐 Autenticação

A API usa **JWT (JSON Web Token)**. Para acessar os endpoints protegidos:

### Obter token

```http
POST /api/token/
Content-Type: application/json

{
    "username": "seu_usuario",
    "password": "sua_senha"
}
```

**Resposta:**
```json
{
    "access": "eyJ0eXAiOiJKV1Qi...",
    "refresh": "eyJ0eXAiOiJKV1Qi..."
}
```

### Usar o token nas requisições

```http
GET /api/v1/pacientes/
Authorization: Bearer eyJ0eXAiOiJKV1Qi...
```

### Renovar o access token

```http
POST /api/token/refresh/
Content-Type: application/json

{ "refresh": "eyJ0eXAiOiJKV1Qi..." }
```

### Logout (revogar token)

```http
POST /api/token/blacklist/
Content-Type: application/json

{ "refresh": "eyJ0eXAiOiJKV1Qi..." }
```

---

## 📡 Endpoints

### Dashboard

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/v1/dashboard/` | Métricas gerais (consultas, financeiro, estoque) |

### Usuários

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/v1/usuarios/` | Listar usuários |
| POST | `/api/v1/usuarios/` | Criar usuário |
| GET | `/api/v1/usuarios/me/` | Usuário autenticado atual |
| GET/PUT/PATCH/DELETE | `/api/v1/usuarios/{id}/` | Detalhar/editar/excluir |

### Pacientes

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/v1/pacientes/` | Listar pacientes |
| POST | `/api/v1/pacientes/` | Criar paciente |
| GET | `/api/v1/pacientes/buscar/?q=termo` | Busca rápida |
| GET | `/api/v1/pacientes/{id}/consultas/` | Consultas do paciente |
| GET | `/api/v1/pacientes/{id}/prontuarios/` | Prontuários do paciente |
| GET | `/api/v1/pacientes/{id}/financeiro/` | Lançamentos do paciente |

**Filtros disponíveis:**
- `?nome=joao` — filtrar por nome
- `?cpf=123` — filtrar por CPF
- `?plano=unimed` — filtrar por plano
- `?nascimento_de=1990-01-01&nascimento_ate=2000-12-31` — faixa de nascimento
- `?search=<termo>` — busca global
- `?ordering=nome_completo|-criado_em` — ordenação

### Consultas

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/v1/consultas/` | Listar consultas |
| POST | `/api/v1/consultas/` | Agendar consulta |
| GET | `/api/v1/consultas/hoje/` | Consultas de hoje |
| PATCH | `/api/v1/consultas/{id}/confirmar/` | Confirmar consulta |
| PATCH | `/api/v1/consultas/{id}/cancelar/` | Cancelar consulta |
| PATCH | `/api/v1/consultas/{id}/realizar/` | Marcar como realizada |

**Filtros:** `?status=agendada`, `?dentista_id=1`, `?data_de=2025-01-01`, `?tipo=retorno`

### Dentistas

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/v1/dentistas/` | Listar dentistas |
| GET | `/api/v1/dentistas/{id}/agenda/?data=YYYY-MM-DD` | Agenda do dentista |

### Financeiro

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/v1/financeiro/` | Listar lançamentos |
| GET | `/api/v1/financeiro/resumo/` | Resumo (saldo, totais) |

**Filtros:** `?tipo=receita`, `?status=pendente`, `?forma_pagamento=pix`, `?vencimento_de=2025-01-01`

### Estoque

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/v1/estoque/` | Listar itens |
| GET | `/api/v1/estoque/alertas/` | Itens críticos e vencidos |

**Filtros:** `?categoria=anestesico`, `?estoque_baixo=true`, `?validade_ate=2025-12-31`

---

## 📖 Documentação Interativa

Com o servidor rodando, acesse:

| URL | Descrição |
|-----|-----------|
| `http://localhost:8000/api/docs/` | **Swagger UI** — interface interativa |
| `http://localhost:8000/api/redoc/` | **ReDoc** — documentação limpa |
| `http://localhost:8000/api/schema/` | Schema OpenAPI (JSON/YAML) |

---

## 🗄️ Painel Administrativo

Acesse em `http://localhost:8000/admin/` com o superusuário criado.

Funcionalidades do admin:
- Listagens com filtros, busca e ordenação para todos os modelos
- Badges coloridos de status (consultas, financeiro)
- Inline de procedimentos no prontuário
- Alertas visuais de estoque baixo

---

## 🧪 Verificação rápida

```bash
# Checar configuração do Django
python manage.py check

# Verificar migrations pendentes
python manage.py showmigrations

# Criar superusuário
python manage.py createsuperuser
```

---

## 📂 Estrutura do Projeto

```
consultorio-odontologico-django/
├── config/
│   ├── settings.py       # Configurações do projeto
│   ├── urls.py           # URLs raiz
│   ├── wsgi.py
│   └── asgi.py
├── principal/
│   ├── models.py         # Modelos de dados
│   ├── serializers.py    # Serializers DRF
│   ├── views.py          # ViewSets e Views
│   ├── urls.py           # Roteamento da API
│   ├── filters.py        # FilterSets
│   ├── admin.py          # Painel administrativo
│   └── migrations/       # Migrations do banco
├── .env.example          # Exemplo de variáveis de ambiente
├── requirements.txt      # Dependências Python
└── manage.py
```

---

## 🔒 Segurança em Produção

Antes de fazer deploy em produção:

1. **Gere uma SECRET_KEY segura:**
   ```bash
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```
2. Defina `DEBUG=False` no `.env`
3. Configure `ALLOWED_HOSTS` com seu domínio
4. Use PostgreSQL em vez de SQLite
5. Configure um servidor de arquivos estáticos (ex: nginx)
6. Use HTTPS

---

## 📄 Licença

Este projeto está sob a licença MIT.
