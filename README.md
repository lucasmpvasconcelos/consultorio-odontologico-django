# 🦷 Sistema de Gestão para Consultório Odontológico

Sistema desenvolvido em **Python e Django** para gerenciamento completo de consultórios odontológicos, permitindo o controle de pacientes, dentistas, consultas, prontuários, estoque e financeiro.

## 🚀 Funcionalidades

### 👤 Gestão de Usuários

* Autenticação e autorização de usuários
* Perfis de acesso:

  * Administrador
  * Dentista
  * Recepcionista

### 🦷 Gestão de Pacientes

* Cadastro completo de pacientes
* Informações pessoais
* Convênios
* Histórico de atendimento

### 👨‍⚕️ Gestão de Dentistas

* Cadastro de profissionais
* Especialidades
* Informações de contato

### 📅 Agendamento de Consultas

* Controle de consultas
* Associação entre paciente e dentista
* Histórico de atendimentos

### 📋 Prontuário Odontológico

* Anamnese
* Diagnóstico
* Plano de tratamento
* Prescrições
* Radiografias
* Odontograma em formato JSON

### 🛠 Procedimentos

* Cadastro de procedimentos odontológicos
* Associação aos prontuários
* Controle de valores cobrados

### 💰 Controle Financeiro

* Receitas e despesas
* Controle de lançamentos financeiros
* Acompanhamento financeiro da clínica

### 📦 Controle de Estoque

* Cadastro de materiais e insumos
* Controle de quantidade
* Alerta de estoque mínimo

---

## 🛠 Tecnologias Utilizadas

* Python 3.14
* Django 6
* Django REST Framework
* SQLite3
* HTML
* CSS
* Git
* GitHub

---

## 📂 Estrutura do Projeto

```text
consultorio_odonto/
│
├── config/
├── principal/
│   ├── models.py
│   ├── views.py
│   ├── serializers.py
│   ├── urls.py
│   └── admin.py
│
├── manage.py
├── requirements.txt
└── README.md
```

---

## ⚙️ Como Executar o Projeto

### 1. Clonar o repositório

```bash
git clone https://github.com/lucasmpvasconcelos/consultorio-odontologico-django.git
```

### 2. Entrar na pasta do projeto

```bash
cd consultorio-odontologico-django
```

### 3. Criar ambiente virtual

```bash
python -m venv .venv
```

### 4. Ativar ambiente virtual

Windows:

```bash
.venv\Scripts\activate
```

Linux/Mac:

```bash
source .venv/bin/activate
```

### 5. Instalar dependências

```bash
pip install -r requirements.txt
```

### 6. Aplicar migrações

```bash
python manage.py migrate
```

### 7. Criar superusuário

```bash
python manage.py createsuperuser
```

### 8. Executar o servidor

```bash
python manage.py runserver
```

Acesse:

```text
http://127.0.0.1:8000/admin/
```

---

## 📈 Próximas Implementações

* API REST completa
* Autenticação JWT
* Dashboard com indicadores
* Relatórios PDF
* Agendamento online
* Integração com frontend React
* Deploy em nuvem

---

## 👨‍💻 Desenvolvedor

**Lucas Vasconcelos**

📌 Em transição para a área de Tecnologia da Informação, com foco em Python, Backend, Automação e Inteligência Artificial.

GitHub:
https://github.com/lucasmpvasconcelos

Instagram:
https://instagram.com/techhub.dev

---

⭐ Se este projeto foi útil, deixe uma estrela no repositório.
