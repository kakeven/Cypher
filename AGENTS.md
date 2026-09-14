# AGENTS.md — Guia para agentes de IA no projeto Cypher

## Objetivo

Cypher é um aplicativo desktop de **finanças pessoais** (controle de gastos, orçamentos, metas de poupança). Distribuição alvo: instalador único (`.exe`/`.dmg`/`.AppImage`) com backend Python embarcado. Este repositório contém **a versão de desenvolvimento local** desse app, com frontend Vue 3 e backend FastAPI rodando como processos separados.

Toda a verdade sobre o estado atual do projeto (o que está pronto, o que falta, convenções, decisões registradas) vive em **`project.md`**. **Leia `project.md` antes de tomar decisões não triviais.** Ele é o snapshot vivo do projeto e deve ser atualizado sempre que o estado mudar.

## Stack

| Camada | Tecnologia |
|---|---|
| Frontend | Vue 3 + Vite + Vue Router + Pinia |
| Package manager | pnpm (engines node `^22.18 \|\| >=24.12`) |
| Backend | Python 3.14 + FastAPI + Uvicorn + SQLAlchemy 2.0 + Pydantic v2 |
| Banco | SQLite (arquivo local; em Docker, volume nomeado `sqlite-data`) |
| Testes backend | pytest + httpx |
| Gráficos | Chart.js / Plotly (planejado, ainda não integrado) |
| Cotações | yfinance (planejado, ainda não integrado) |
| Build desktop | electron-builder (planejado) |
| Dev container | Docker Compose (`docker-compose.yml` na raiz) |

## Comandos principais

```powershell
# Subir ambiente completo (backend :8000 + frontend :5173)
docker compose up --build

# Backend isolado (sem Docker)
cd backend && python -m pip install -r requirements.txt && python -m uvicorn main:app --reload --port 8000

# Frontend isolado (sem Docker)
cd frontend && pnpm install && pnpm dev

# Testes backend
python -m pytest backend/tests -q

# Build de produção do frontend
pnpm --dir frontend build

# Lint do frontend
pnpm --dir frontend lint
```

## Onde está cada coisa

- **Requisitos funcionais/não-funcionais completos:** `cypher-requisitos-v11-realocado.docx` (não editar; é a fonte de produto).
- **Estado atual, gaps e decisões:** `project.md` ← **leia sempre antes de mudanças não triviais.**
- **Planos anteriores / handover de planejamento:** `.kilo/plans/*.md`.
- **Backend:** `backend/main.py` (API única, ~300 linhas).
- **Frontend:** `frontend/src/views/` (telas) e `frontend/src/components/` (componentes reutilizáveis).
- **Configuração do banco:** env var `CYPHER_DATABASE_URL` (default local `backend/cypher.db`, em Docker `sqlite:////app/data/cypher.db`).

## Regras para agentes

1. **Antes de implementar algo não trivial, leia `project.md`** para saber o que já existe e quais convenções seguir.
2. **Após mudanças significativas, atualize `project.md`** (seção "O que está implementado" + "O que NÃO está implementado" + "Decisões registradas").
3. **Sem comentários no código** salvo quando explicitamente solicitado.
4. **Mensagens de erro e respostas em português** (consistente com o que já existe em `backend/main.py`).
5. **Não introduza segredos** (chaves, tokens, senhas) em código ou commits.
6. **Não faça commit** sem solicitação explícita do usuário.
7. **Respeite a stack:** não adicionar dependências sem justificativa. O backend é FastAPI/SQLAlchemy; o frontend é Vue 3 + Pinia. Evite misturar paradigmas.
8. **CORS** está liberado só para `localhost:5173` e `127.0.0.1:5173`. Não amplie sem motivo.
9. **Modelos do banco** são derivados de `Base.metadata.create_all(engine)` no startup — sem migrations formais ainda. Se criar novos modelos, adicione-os no mesmo arquivo `backend/main.py` ou em módulo importado por ele.
10. **Docker:** preferir `docker compose` (plugin V2), não `docker-compose` standalone.

## Referências rápidas

- Regras de negócio e modelo de dados: `project.md` + `cypher-requisitos-v11-realocado.docx` seção 4 e 5.
- Endpoints disponíveis: `project.md` seção "Endpoints expostos" ou `http://localhost:8000/docs` (Swagger UI).
- Estrutura de pastas: `project.md` seção "Estrutura de pastas".

## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

When the user types `/graphify`, use the installed graphify skill or instructions before doing anything else.

Rules:
- For codebase questions, first run `graphify query "<question>"` when graphify-out/graph.json exists. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- Dirty graphify-out/ files are expected after hooks or incremental updates; dirty graph files are not a reason to skip graphify. Only skip graphify if the task is about stale or incorrect graph output, or the user explicitly says not to use it.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).
