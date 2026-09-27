# AGENTS.md — Framework Analytics Platform (FAP)

> **Este documento orienta agentes (AI/code helpers) que trabalharem neste projeto.**
> Mantenha-o atualizado quando adicionar novas convenções, rotinas ou mudanças breaking.

---

## 1. Visão geral

**FAP — Framework Analytics Platform** é uma plataforma Flask 3 + PostgreSQL para mineração de repositórios de software. Coleta *code churn* (PyDriller) e métricas sociais (GitHub API), armazena métricas de sustentabilidade e exibe dashboard interativo com Plotly.js.

- **Backend:** Python 3.12, Flask, Flask-Login, APScheduler, waitress (produção)
- **Banco:** PostgreSQL com schema idempotente ( `sql/schema.sql` )
- **Coleta:** PyDriller (commits, churn, Bus Factor, churn relativo) + GitHub API (TTFR, issues, releases, contribuidores)
- **Frontend:** Plotly.js, HTML templates Jinja2, JS vanilla com escaping consistente
- **Testes:** pytest (~60 testes), pyflakes (lint), cobertura de math/pure functions, mock da rede, smoke de rotas

---

## 2. Arquitetura e convenções

### Diretórios-chave

| Diretório | Conteúdo |
|---|---|
| `src/app.py` | Rotas Flask, orquestração da coleta, status global, initialization |
| `src/config.py` | Variáveis de ambiente (`os.getenv`), `PROJ_ROOT`, `DB_CONFIG`, `GITHUB_TOKEN`, `MESES_ANALISE` |
| `src/database.py` | Pool `ThreadedConnectionPool`, helpers de upsert, criptografia Fernet de tokens, migrations embutidas em `init_schema()` |
| `src/analises.py` | Matemática pura: score sustentabilidade (0–100), curva de concentração de conhecimento |
| `src/collect/pydriller_collect.py` | Motor PyDriller: clonagem, commits por dia, autor, lines add/del, Bus Factor, churn relativo, LOC |
| `src/collect/github_metrics.py` | GitHub API: issues (state=all, paginated), TTFR (mediana first comment humano), releases, contribuidores |
| `src/status.py` | Estado da coleta compartilhado entre threads (lock + dict) — exposto via `/api/coleta/status` |
| `src/relatorio.py` | Geração de `.docx` com python-docx + matplotlib gráficos em memória |
| `tests/` | 60 testes: matemática pura, utilitários dos coletores, helpers de banco, smoke das rotas |
| `data/repos/` | Clones git temporários (um por repositório, `owner__nome` para evitar colisão de nomes) |
| `static/js/` | JS do dashboard: polling, gráficos Plotly, CRUD, escapa com `esc()` |
| `templates/` | Jinja2: `base.html`, `login.html`, `meus_repos.html`, `repo_detalhe.html`, `snapshot.html`, `comparar.html` |

### Importações

- **Nunca** faça `from src import ...` fora de `src/` — o `conftest.py` injeta `sys.path` na raiz.
- Use imports relativos/absolutos já existentes nos módulos (ex.: `from database import connection, init_schema`).
- Os módulos de `collect/` importam `from collect.github_metrics import ...` e `from collect.pydriller_collect import ...`.

---

## 3. Pontos fortes (já consolidados)

- Schema idempotente + migrations manuais em `init_schema()` — roda em CI com banco vazio.
- Criptografia de token OAuth com Fernet + PBKDF2 200k (`database.py:24-58`) + tolerância a legado.
- Lock de coleta por repo (`_coleta_lock` em `app.py:671`) + fila de espera com timeout 2h.
- Escape JS consistente: `esc()` em todos os `static/js/*` + `tojson` nos templates (`meus_repos.html:74`, `comparar.html:62`).
- CSV injection protection: `_celula_csv()` em `app.py:630-635`.
- `/login/dev` restrito a `127.0.0.1`/`.::1` quando OAuth não configurado (`app.py:161`).
- Testes unitários puros (sem banco) em `tests/test_analises.py`, `tests/test_coletor.py`, `tests/test_coletores_mock.py`.
- `pyflakes src tests` limpo.

---

## 4. Problemas abertos (categorizados)

### Média severidade — correção de dados

| # | Arquivo:Linha | Descrição | Correção sugerida |
|---|---|---|---|
| 1 | `analises.py:46-48` | Curva de concentração filtra `mes >= inicio` mas `mes` é dia 01 e `inicio` tem dia arbitrário (ex.: 27) → **mês inicial da janela é perdido**. | Normalizar `inicio` para dia 1 antes de passar: `inicio.replace(day=1)` ou ajustar a query. |
| 2 | `database.py:368-372` | `insert_metrica_autor_mensal` deleta `mes >= inicio` — o mês parcial inicial **nunca é limpo**, então autores que saíram ficam com contagem antiga. | Considerar limpar também o mês onde `mes < inicio` mas próximo (ex.: `mes >= date_trunc('month', inicio)`). |
| 3 | `app.py:445-468` | `commits` no resumo da API vem da janela corrente, mas `bus_factor/ttfr/churn` vêm da última coleta — **componentes medem períodos diferentes** se coleta atrasada. | Garantir que a janela de `commits` coincida com `periodo_inicio/fim` da sustentabilidade. |
| 4 | `app.py:206-209` | Status da coleta é **global** — qualquer usuário logado vê progresso de todos os repos, e o dashboard casa por nome de repo, podendo mostrar "coletando" do repo de outro usuário. | Considerar status por-usuário ou adicionar aviso de multi-tenant. |
| 5 | `pydriller_collect.py:64` | Autor identificado por **nome** (`commit.author.name`) — "João Silva" x "joão silva" se separam; troca de nome infla/divide Bus Factor e curva. | Armazenar also `commit.author.email` e usar como chave única (exigiria alteração de schema). |

### Baixa severidade — robustez/segurança

| # | Arquivo:Linha | Descrição | Correção sugerida |
|---|---|---|---|
| 6 | `github_metrics.py:57-66` | `_parse_owner_repo` quebra em URLs com paths extras: `github.com/owner/repo/tree/main` → `("tree","main")` → 404 confuso. | Já pega `parts[-2], parts[-1]` (ignora tree/blob/etc.) — sem mudança se já for esse o comportamento intencional, mas adicionar teste para `/tree/main`. |
| 7 | `database.py:15-21` | `DB_CONFIG` sem `connect_timeout` — connections penduradas se o banco cair. | Adicionar `connect_timeout`: `int(os.getenv("DB_CONNECT_TIMEOUT", "10"))`. |
| 8 | `app.py:47` | `SESSION_COOKIE_SECURE` não definido — cookie transmitido em HTTP mesmo atrás de HTTPS se houver mixed content. | `app.config["SESSION_COOKIE_SECURE"] = True` (sempre atrás de proxy HTTPS) ou condicional. |
| 9 | `app.py:200-203` | Endpoint `/api/health` sem rate limit — exposto a DDOS simples em produção. | Rate limit simples (ex.: `flask-limiter` ou in-memory com dicionário + `time.time()`). |
| 10 | `pydriller_collect.py:131-135` | `subprocess.run(..., capture_output=True)` sem `check=True` — falha silenciosa em `ls-files`. | Adicionar `check=True` ou validar `returncode`. |
| 11 | `app.py:686-698` | Threads sem bound: cada POST `/repos` durante coleta cria thread que espera 2h. | Contador de threads ativas ou usar `asyncio` + `await` em vez de threads. |
| 12 | `requirements.txt` | Versões fixadas mas sem `hash` (não é `requirements.txt` com `sri`) — pode quebrar se PyPI remover versão. | Bloquear versão é ok, mas testar `pip install -r requirements.txt` periodicamente. |

---

## 5. Prioridade de correções (próximos 2 sprints)

### Sprint 1 (alta impacto, baixo risco)
1. **Bug da janela da curva** (`analises.py:46-48` + `app.py:417,490`) — normalizar `inicio` para dia 1. Isso alinha curva, autor-mensal e score.
2. **Bug do `_parse_owner_repo`** (`github_metrics.py:57-66`) — já funciona pegando últimos 2 segmentos, adicionar teste parametrizado para `.../tree/main`.
3. **`connect_timeout`** (`database.py`) — 1 linha, previne connections hanging.

### Sprint 2 (média impacto)
4. **Limpeza do mês inicial** (`database.py:368-372`) — ajustar delete para considerar mês de início corretamente.
5. **Token cookie secure** (`app.py:47`) — 1 linha, hardening de segurança.
6. **`subprocess check=True`** (`pydriller_collect.py:131`) — tolerância a repos corrompidos.

### Backlog (baixo impacto / futuro)
7. Status por-usuário vs global (`app.py:206`).
8. Autor por e-mail em vez de nome (`pydriller_collect.py:64`).
9. Rate limit em `/api/health` e `/callback`.
10. Migração para alembic vs migrations embutidas.

---

## 6. Testes

### Como rodar

```bash
# Na raiz do projeto (já com venv ativo)
pytest -q
```

Isso roda todos os testes (requer PostgreSQL; CI roda com `postgres:16` service).

### Convenções de teste

- **Testes puros (sem banco/ rede):** `tests/test_analises.py`, `tests/test_coletor.py` — podem rodar offline.
- **Testes com mock da rede:** `tests/test_coletores_mock.py` — usa `responses` para registrar respostas HTTP.
- **Testes de integração (banco):** `tests/test_database.py`, `tests/test_relatorio_snapshot.py`, `tests/test_smoke.py` — dependem do `conftest.py` que roda `init_schema()` e seta `FAP_SEM_AUTOCOLETA=1`.
- **Nunca modifique o schema nos testes** sem também atualizar `conftest.py` e a migration `init_schema()`.

### Adicionando um novo teste

1. Coloque em `tests/` seguindo o padrão existente (parametrizado quando possível).
2. Se tocar banco, crie fixture `repo_do_teste` (já existente em `tests/test_relatorio_snapshot.py`) ou `logado` em `tests/test_smoke.py`.
3. Rode `pytest -q` para verificar que não quebrou nada.
4. Se for função pura (nenhum import de `src/` que toque banco), pode rodar `pytest -k nome_teste -q` isolado.

---

## 7. Lint / Formatação

- `pyflakes src tests` → deve permanecer **limpo**.
- Não há config `ruff`/`black`/`isort` definida no momento. Se adicionar, seguir convensão do projeto:
  - Python 3.12
  - Black versão >= 23.x (se adotar, executar `black src tests` e commitar).
  - Isort para imports padrão.
- O CI usa apenas `pyflakes` + `pytest` (`.github/workflows/lint.yml`).

---

## 8. Como executar localmente (resumo)

```bash
# 1. Ambiente virtual
python -m venv fap_env
.\fap_env\Scripts\activate
pip install -r requirements.txt

# 2. Banco de dados
psql -U postgres -d postgres -c "CREATE DATABASE fap;"

# 3. .env (copiar .env.example e preencher)
copy .env.example .env
# Editar: DB_PASSWORD, GITHUB_TOKEN, SESSION_SECRET, GITHUB_CLIENT_ID/SECRET opcional

# 4. Aplicar schema (feito automaticamente no boot, ou manualmente)
python -c "from src.database import init_schema; init_schema()"

# 5. Iniciar
python src/app.py   # ou waitress serve src.app:app
# Acessar http://127.0.0.1:5000
```

### Docker (opcional)

```bash
docker compose up --build
# Sobe app + PostgreSQL na mesma rede; app em http://localhost:5000
```

---

## 9. Convenções de código (do que já observado)

- **Naming:** snake_case para funções/variáveis, ALL_CAPS para constantes (`TETO_COMMITS`, `PISO_TTFR_DIAS`, etc.).
- **Docstrings:** presente em todos os módulos (`"""..."""`); funções expostas têm docstring explicando parâmetros/retorno.
- **Tratamento de erro:** `try/except` geral com `log.exception(...)` + retorno de valor seguro (lista vazia, `None`, JSON de erro).
- **Thread safety:** uso de `_coleta_lock` (threading.Lock) ao atualizar estado global; conexões do pool são devolvidas em `finally`.
- **SQL injection:** todos os queries usam parâmetros (`%s`) com `psycopg2` — nenhum `f-string` puro em SQL.
- **CSV injection:** `_celula_csv()` protege contra fórmulas `=+@` no export.
- **XSS:** escaping `esc()` em JS; `tojson` nos templates Jinja2; nunca `markup.unsafe()` nem `|safe` sem necessidade.

---

## 10. Perguntas frequentes para agentes

<details>
<summary>Como adicionar uma nova métrica?</summary>
1. Calcular a métrica nos coletores (`collect/pydriller_collect.py` ou `collect/github_metrics.py`).
2. Inserir no banco via `database.py` (ex.: `insert_metrica_sustentabilidade`).
3. Expor via API em `src/app.py` (rota `/api/repo/<id>/resumo` ou similar).
4. Usar em `analises.py` se for cálculo matemático (score/curva).
5. Adicionar template no HTML correspondente (`repo_detalhe.html` ou `snapshot.html`).
6. Testar em `tests/` (mock ou banco).
</summary>

<details>
<summary>Por que a curva falta o mês inicial?</summary>
`mes` no banco sempre é dia 01 (via `agregar_por_mes_autor`, linha 96: `tmp["mes"] = ...dt.to_period("M").dt.start_time.date`). O `inicio` vem de `now - MESES_ANALISE` que mantém o dia do mês atual (ex.: 27). O filtro `mes >= '2026-09-27'` ignora `2026-09-01`. A correção é normalizar `inicio` para dia 1 antes de passar adiante.
</summary>

<details>
<summary>Preciso rodar pytest com banco?</summary>
Depende. `tests/test_analises.py` e `tests/test_coletor.py` rodam sem banco (pure functions + mock). Tudo que tiver `db` na fixture depende do `conftest.py` que cria as tabelas automaticamente. Se estiver adicionando teste novo que toca banco, rode `pytest -q` na raiz (cria schema sozinho).
</summary>
</details>

---
*Última atualização: $(date +%Y-%m-%d). Este arquivo faz parte do fluxo de trabalho do agente FAP. Mantenha-o consistente com as mudanças de código.*