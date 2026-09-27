# TRABALHO.md — Fila de tarefas compartilhada (3 abas)

> Regras: marque `em andamento (nome)` antes de editar e `feito (hash)` depois.
> Uma aba commita por vez — `git add` explícito, nunca `git add -A`.
> Nunca reinicie a app/postgres sem avisar aqui primeiro.

## Estado do projeto
- Últimos commits: `b08233f` (CI restaurado), `51f4997` (10 correções da auditoria)
- Suíte: 75/75 testes, pyflakes limpo, CI verde, app no ar (health 200)
- Postgres: sem serviço — pode cair; subir com pg_ctl (ver AGENTS.md)
- Banco: coluna renomeada para `ttfr_mediano_dias`; migração idempotente no boot

## Fila de tarefas

### Frontend (Kimi K3)
- [ ] **K1 — Janela de exibição das telas = período da última coleta**
      Hoje as telas recalculam `data corrente − 6m` (`app.py` em
      `_dados_comparacao` ~:399 e `api_repo_resumo` ~:445) e os números
      driftam entre coletas. Trocar para usar o `periodo_inicio`/`periodo_fim`
      da última coleta do repo (`Metrica_Sustentabilidade`) — toca `app.py`
      (coordenar com GLM via este arquivo) e nenhum JS. Mantenha o snapshot
      como está (já usa períodos fixos).

### Testes e docs (Nemotron 3.5)
- [ ] **N1 — Testes da interseção e do CSV**
      `tests/`: (a) `_tarefa_mineracao` com os dois motores mockados —
      cobrir alvo = interseção (`comuns`), união de `falhas` e mensagens;
      (b) `_celula_csv` (app.py:630) — `=`, `+`, `-`, `@`, None, texto normal.
- [ ] **N2 — Pin das deps de teste no CI**
      `.github/workflows/lint.yml`: `pip install -r requirements.txt
      pytest responses` → fixar versões (ex.: `pytest==8.4.2 responses==0.26.3`
      — conferir as versões instaladas no venv antes).
- [ ] **N3 — README: endpoints e testes novos**
      Documentar `/repo/<id>/relatorio`, `/snapshot` + `/snapshot.csv`,
      `/comparar?ids=`, logout via POST e a suite atual (75 testes).

### Backend (GLM — coordenador)
- [ ] **G1 — Pool com health-check + connect_timeout**
      `database.py`: ping (`SELECT 1`) no checkout do `getconn()`; se falhar,
      descartar a conexão e recriar o pool (postgres dessa máquina cai às
      vezes). `DB_CONFIG` com `connect_timeout=5` (config.py).
- [ ] **G2 — Race 404 + origin/HEAD**
      `app.py` (`api_repo_resumo` ~:444, `api_repo_github` ~:502):
      `if not repo: abort(404)` antes de usar `repo[...]`.
      `pydriller_collect.py` (~:42): `git remote set-head origin -a` antes do
      `reset --hard origin/HEAD` (default branch renomeada deixava o reset
      numa branch velha).
- [ ] **G3 — Revisar/mergear commits das outras abas + CI**
      Validar suíte/pyflakes após cada commit dos colegas e conferir Actions.
- [ ] **G4 — `contar_loc`: log em falha silenciosa**
      `pydriller_collect.py:130-149`: hoje falha conta 0 linhas sem log —
      adicionar `log.warning` com o motivo.

## Aguardando decisão do usuário (não executar sem ele decidir)
- [ ] **D1 — Bots no Bus Factor?** Hoje `dependabot[bot]` etc. contam como
      "pessoa" e inflam o BF. Filtrar muda os números do artigo.
- [ ] **D2 — pandas 3**: `pd.read_sql` com psycopg2 cru é deprecado. Migração
      para consultas por cursor puro (sem SQLAlchemy novo) — decidir quando.
- [ ] **D3 — SESSION_COOKIE_SECURE**: só com HTTPS/proxy (Docker) — em
      localhost quebraria o login. Env-gate quando houver deploy.
