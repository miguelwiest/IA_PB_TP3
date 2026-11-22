# Sistema Inteligente de Atendimento ao Cliente - Projeto de Bloco (TP3)

Este repositório contém a entrega do **Trabalho Prático 3 (TP3)** do Projeto de Bloco (Análise e
Segurança de Agentes de IA) do **Instituto Infnet** — "Classificação de intenções + Testes de
segurança + API".

> **Nota sobre TP1/TP2 → TP3:** o enunciado do TP3 pede que o repositório seja criado "a partir de
> um clone do repositório do TP2". Como o **TP2 não introduziu mudanças estruturais relevantes**
> em relação ao TP1 (mesma EDA, mesma API, mesmas credenciais in-code), o TP2 foi tratado como uma
> cópia direta do TP1 (ver `PB/TP2/README.md`), e este TP3 parte diretamente dessa base,
> evoluindo-a com tudo o que o enunciado do TP3 exige (banco SQLite real com múltiplos usuários,
> BOLA, rate limiting, CI com GitHub Actions, auditoria ZAP e planejamento do modelo de
> classificação).

---

## Objetivo do Projeto

O objetivo deste projeto é consolidar as bases estatísticas, arquiteturais e de segurança de um
**Sistema de Atendimento ao Cliente com IA** antes de treinar o classificador de intenções real
(TP4/TP5):
1. **EDA consolidada (TP1+TP2+TP3)**: um único notebook (`eda/eda_tp3.ipynb`) reunindo a
   exploração de dados original, um experimento real de regressão linear e a formalização do
   problema de classificação de intenções.
2. **API FastAPI com persistência real (SQLite)**: substituição do usuário único in-code por um
   banco de dados com múltiplos usuários e recursos (tickets) de donos diferentes, permitindo
   testar controles de autorização reais (anti-BOLA).
3. **Testes automatizados de segurança** (pytest + TestClient): autenticação, autorização/BOLA,
   validação de entrada, rate limiting e proteção de rotas.
4. **Integração contínua** com GitHub Actions executando a suíte de testes a cada push.
5. **Auditoria de segurança com OWASP ZAP** contra a API em execução, com correção dos achados
   Medium/High e evidência da correção.
6. **Planejamento da próxima etapa** (`others/planejamento_tp3.md`): modelo candidato,
   vetorização de texto e alvo do teste adversarial (placeholder, pendente de pareamento).

---

## Estrutura do Repositório

```text
TP3/
├── README.md                          # Este arquivo
├── requirements.txt                   # Dependências completas do projeto (EDA + API)
├── Miguel_Andrade_PB_TP3.md           # Entregável final (nome + link do repositório)
├── data/
│   └── customer_support_tickets.csv   # Dataset de tickets de suporte ao cliente
├── eda/
│   └── eda_tp3.ipynb                  # Notebook único, EDA consolidada TP1+TP2+TP3
├── fastapi/
│   ├── main.py                        # App FastAPI, CORS, rate limiter, inicialização do SQLite
│   ├── rate_limit.py                  # Limiter compartilhado (slowapi)
│   ├── sqlite_database.py             # Criação do schema SQLite (users, tickets)
│   ├── sqlite_populate.py             # População com 2 usuários + tickets de donos diferentes
│   ├── database.db                    # Banco SQLite já populado (gerado por sqlite_populate.py)
│   ├── requirements.txt               # Dependências da API
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py                 # Schemas Pydantic (entrada com extra="forbid")
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── health.py                  # GET /health
│   │   ├── auth.py                    # POST /auth/token (rate limited) e GET /auth/me
│   │   ├── predict.py                 # POST /predict (protegido por JWT)
│   │   └── tickets.py                 # GET /tickets/{id} (protegido + anti-BOLA)
│   └── security/
│       ├── __init__.py
│       └── auth.py                    # JWT, Bcrypt, OAuth2PasswordBearer, usuários via SQLite
├── tests/
│   ├── test_api.py                    # Testes herdados do TP1 (saúde, auth, predict)
│   └── test_security_tp3.py           # 5 testes de segurança exigidos pelo TP3
├── zap/
│   ├── zap_report_run1.html           # Relatório ZAP da 1a rodada (achados antes da correção)
│   ├── zap_report_run2.html           # Relatório ZAP da 2a rodada (após correção)
│   └── scan_passivo_zap_TP3.md        # Análise dos findings Medium/High e evidência da correção
├── .github/workflows/
│   └── ci.yml                         # Pipeline de CI (checkout, setup-python, pytest tests/ -v)
└── others/
    ├── planejamento_tp3.md            # Modelo candidato, CountVectorizer, alvo adversarial
    ├── CIA.csv / CIA.png / DFD.drawio / DFD.png   # Herdados do TP1 (modelagem de segurança)
```

---

## Instalação e Pré-requisitos

### 1. Clonar o repositório
```bash
git clone <URL_DO_REPOSITORIO>
cd <NOME_DO_REPOSITORIO>
```

### 2. Criar e ativar um ambiente virtual (opcional, mas recomendado)
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux / MacOS
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar as dependências
```bash
pip install -r requirements.txt
```

---

## Criação e População do Banco de Dados (SQLite)

A API não usa mais um dicionário de usuários in-code: as credenciais e os tickets de exemplo vivem
em `fastapi/database.db` (SQLite), com duas tabelas:
- `users`: usuários e hash bcrypt da senha.
- `tickets`: tickets de suporte, cada um com um `owner_username` — usado para o controle
  anti-BOLA em `GET /tickets/{id}`.

O arquivo `fastapi/database.db` **já é entregue populado** neste repositório, mas pode ser
recriado/recarregado a qualquer momento:

```bash
cd fastapi
python sqlite_database.py   # cria o schema (idempotente)
python sqlite_populate.py   # popula usuários + tickets de exemplo (idempotente)
```

Usuários de exemplo criados (ver `fastapi/sqlite_populate.py`):

| username            | senha            | dono do ticket # |
|---------------------|------------------|------------------|
| `admin`              | `AdminInfnet2026!` | 1 |
| `cliente_fernanda`   | `Fernanda2026!`    | 2 |

> A própria API chama `sqlite_populate.populate()` no startup (`fastapi/main.py`), então mesmo que
> `database.db` seja apagado, ele é recriado e populado automaticamente ao subir a aplicação.

---

## Como Executar a API

```bash
cd fastapi
uvicorn main:app --reload --port 8089
```

A API estará acessível em: `http://127.0.0.1:8089`
- **Swagger UI:** `http://127.0.0.1:8089/docs`
- **ReDoc:** `http://127.0.0.1:8089/redoc`

### Principais rotas

| Rota | Método | Autenticação | Descrição |
|---|---|---|---|
| `/health` | GET | pública | Status operacional da API |
| `/auth/token` | POST | pública (form-data) | Login; **rate limit: 5 req/min por IP** (429 acima do limite) |
| `/auth/me` | GET | JWT (Bearer) | Dados do usuário autenticado |
| `/predict` | POST | JWT (Bearer) | Classificação simulada de intenção do ticket; body validado por Pydantic (`extra="forbid"`) |
| `/tickets/{id}` | GET | JWT (Bearer) | Consulta de ticket por ID; **403** se o ticket não pertencer ao usuário autenticado (anti-BOLA) |

Documentação interativa completa (parâmetros, corpo esperado, respostas e mecanismo de
autenticação de cada rota) disponível em `/docs`.

---

## Execução dos Testes Automatizados

```bash
pytest tests/ -v
```

Suíte com **12 testes**, todos aprovados (ver seção "Resultado real da suíte de testes" abaixo),
incluindo os 5 testes de segurança exigidos pelo TP3 em `tests/test_security_tp3.py`:
1. Autenticação (credenciais válidas/inválidas de um segundo usuário via SQLite)
2. Autorização/BOLA (usuário não acessa ticket de outro dono)
3. Validação de entrada (campo extra não permitido + texto abaixo do tamanho mínimo)
4. Rate limiting (6ª requisição de login na mesma janela retorna 429)
5. Rota protegida sem token (`/tickets/{id}` e `/auth/me` sem `Authorization` retornam 401)

---

## Integração Contínua (GitHub Actions)

Workflow em `.github/workflows/ci.yml`: a cada `push`/`pull_request`, faz checkout, configura
Python 3.12, instala `requirements.txt` e roda `pytest tests/ -v` (a falha de qualquer teste
derruba o job automaticamente, pois o `pytest` retorna código de saída != 0).

> **Limitação documentada:** este workflow foi criado e versionado localmente, mas **não houve
> push para um repositório remoto no GitHub** até o momento desta entrega (não havia repositório
> remoto configurado). Por isso o workflow ainda não foi executado "ao vivo" no GitHub Actions.
> Assim que o repositório remoto for criado e o push for autorizado, o primeiro push disparará a
> execução automática.

---

## Auditoria de Segurança com OWASP ZAP

Auditoria real executada com `zaproxy/zap-stable` (`zap-baseline.py`, via Docker) contra a API
rodando localmente (`http://127.0.0.1:8010`, mapeado para o container como
`http://host.docker.internal:8010`). Relatórios completos em `zap/zap_report_run1.html` (antes da
correção) e `zap/zap_report_run2.html` (depois da correção). Análise detalhada dos findings
Medium/High em `zap/scan_passivo_zap_TP3.md`.

---

## Análise Exploratória de Dados (EDA)

O notebook único `eda/eda_tp3.ipynb` reúne:
- **Seções 1-9 (herdadas do TP1/TP2, sem alteração de conteúdo):** documentação do dataset,
  inspeção inicial, qualidade dos dados, limpeza/preparação, análise univariada e as 3 hipóteses
  de negócio originais.
- **Seção 10 (nova, TP3):** nota explícita sobre a continuidade TP1→TP2→TP3.
- **Seção 11 (nova, TP3 — item 1):** regressão linear real (`word_count` como alvo), com R², RMSE,
  Residual Plot, Q-Q Plot e análise escrita das limitações do modelo.
- **Seção 12 (nova, TP3 — item 2):** formalização do problema de classificação (X = texto do
  ticket, y = `Ticket Type`), tabela e gráfico da distribuição das 5 classes de intenção, e
  justificativa de por que o problema é de classificação (e não de regressão).

---

## Modelagem de Segurança & Diagrama DFD (herdado do TP1)

O diagrama em alta resolução está disponível em [`others/DFD.png`](others/DFD.png) /
[`others/DFD.drawio`](others/DFD.drawio), e a matriz CIA em [`others/CIA.csv`](others/CIA.csv).

### Limites de Confiança (Trust Boundaries)
1. **Trust Boundary 1 (Zona Pública/Não Confiável):** clientes, agentes e requisições externas.
2. **Trust Boundary 2 (Zona Protegida por JWT):** núcleo da API, após validação do token.
3. **Trust Boundary 3 (TP3, novo):** camada de acesso ao SQLite (`fastapi/database.db`) — todo
   acesso a um recurso (`tickets`) passa pela checagem de propriedade (`owner_username`) antes de
   retornar dados, mesmo com um JWT válido de outro usuário.

### Tríade CIA
- **Confidencialidade:** senhas com Bcrypt, segredo JWT via variável de ambiente (com fallback de
  dev documentado), e controle anti-BOLA garantindo que um usuário não leia o ticket de outro.
- **Integridade:** assinatura HMAC-SHA256 (HS256) no JWT; validação estrita de entrada
  (`extra="forbid"`) impedindo injeção de campos não previstos no payload.
- **Disponibilidade:** `/health` para monitoramento e rate limiting em `/auth/token` para mitigar
  esgotamento de recursos por força bruta de credenciais.

---

## Limitações e pendências documentadas nesta entrega

- **Push ao GitHub:** não realizado (sem repositório remoto definido/autorizado até o momento).
  O workflow de CI existe localmente e será validado "ao vivo" assim que o push for feito.
- **PDF da entrega final:** não há ferramenta de geração de PDF disponível neste ambiente; a
  entrega final foi salva como `Miguel_Andrade_PB_TP3.md` (Markdown), conforme permitido quando o
  PDF não está disponível.
- **Alvo do teste adversarial (TP4/TP5):** ainda não existe um colega/grupo pareado para o pentest
  adversarial cruzado; `others/planejamento_tp3.md` documenta um placeholder explícito.

---

## Informações de Entrega (Infnet)

- **Professor:** Tiago Xavier (`tiago.xavier@prof.infnet.edu.br`)
- **Autor (TP3):** Miguel Andrade
- **Repositório Git:** `https://github.com/miguelwiest/IA_PB_TP3`
