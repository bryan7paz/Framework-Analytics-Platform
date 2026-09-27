# AGENTS.md — Instruções para agentes (FAP)

Projeto: **FAP — Framework Analytics Platform** (TCC). App Flask que minera
repositórios públicos do GitHub (PyDriller + API REST), armazena métricas de
sustentabilidade em PostgreSQL e exibe dashboard (Plotly.js) com score 0–100,
curva de concentração de conhecimento, comparador de repos, relatório .docx e
snapshot consolidado.

Leia este arquivo e o `TRABALHO.md` (raiz) antes de qualquer mudança.

## Ambiente (Windows 11, PowerShell 5.1, SEM admin)
- venv: `C:\Users\pazbr\Documents\fap\fap_env` — Python 3.12.4
- PostgreSQL 16: **sem serviço registrado**. Subir/verificar:
  `& "C:\Program Files\PostgreSQL\16\bin\pg_ctl.exe" -D "C:\Users\pazbr\pgdata" start`
  Se já houver processo postgres rodando, não mexa. Creds no `.env` (NUNCA commitar).
- App: matar os PIDs da porta 5000 →
  `fap_env\Scripts\python.exe app.py` (executar de `src/`) →
  smoke em `GET http://127.0.0.1:5000/api/health` (esperar 200).
  Reinicie só quando código/template mudar — e atualize o TRABALHO.md antes.
- Testes: `pytest -q` na raiz. Exigem postgres no ar; `conftest.py` seta
  `FAP_SEM_AUTOCOLETA=1` para o boot não coletar durante os testes.

## Armadilhas do ambiente
- PowerShell **não tem heredoc** (`<<'PY'` falha). Comandos python inline com
  aspas quebram — escreva um script `.py` em
  `C:\Users\pazbr\AppData\Local\Temp\opencode` e execute-o.
- Sempre `$env:PYTHONIOENCODING="utf-8"` antes de rodar python (logs em pt-BR).
- `rg`/`gh` não instalados — use as ferramentas de busca do próprio agente e a
  API REST do GitHub (pública) via requests quando precisar de dados do GitHub.
- Matar processo da porta: `Get-NetTCPConnection -LocalPort 5000 -State Listen`
  → `Stop-Process -Id <pid> -Force`.

## Regras de qualidade (obrigatórias antes de qualquer commit)
1. `pyflakes src tests conftest.py` sem nenhuma saída
2. `pytest -q` verde (hoje: 75 testes)
3. Commit em pt-BR **sem acento**, seguindo o estilo dos últimos
   (`git log --oneline -5`)
4. Push em `origin/master`; CI = pyflakes + testes (`.github/workflows/lint.yml`)
5. Nunca commitar: `.env`, `data/`, `logs*.log`, `__pycache__`, `pg_startup.log`

## Trabalho em 3 abas — coordenação (CRÍTICO)
Todas as abas compartilham este clone e o mesmo banco. Sem as regras abaixo as
abas se atrapalham (conflito de git, app reiniciada no meio do teste do outro).
1. Leia `TRABALHO.md` **antes** de começar e veja o que está livre.
2. Ao pegar uma tarefa, marque nela `em andamento (seu-nome)` **antes** de editar.
3. Uma aba commita por vez. Antes de commitar: `git status` e `git add` explícito
   só dos SEUS arquivos — **nunca `git add -A`** (captura trabalho alheio).
4. NUNCA reinicie a app ou o postgres sem atualizar o TRABALHO.md primeiro.
5. Ao terminar: marque `feito (hash-do-commit)` na tarefa e commite o TRABALHO.md
   junto das suas mudanças.
6. Arquivos de outra área só com coordenação registrada no TRABALHO.md.

## Divisão de áreas
| Agente | Área | Arquivos típicos |
|---|---|---|
| GLM (coordenador) | backend, coletores, banco | `src/app.py`, `src/database.py`, `src/collect/`, `src/analises.py`, `src/relatorio.py` |
| Kimi K3 | frontend | `templates/`, `static/css/`, `static/js/` |
| Nemotron 3.5 | testes e docs | `tests/`, `README.md`, `.github/workflows/` |

## Estado atual
- Veja a fila viva e o estado do projeto em `TRABALHO.md`.
