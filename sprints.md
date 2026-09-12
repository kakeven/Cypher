# Cypher — Sprints de Implementação

Direcionamento da entrega dos requisitos do documento `cypher-requisitos-v11-realocado.docx` (v4.0) em sprints incrementais. Cada sprint deixa o app rodável ao final e pode ser testada de forma isolada.

> **Premissas:**
> - Estado atual: backend FastAPI + frontend Vue 3 servidos como dois processos locais. Ver `project.md` para o que já está pronto.
> - Toda sprint termina com `docker compose up --build` funcionando e testes passando (`pytest backend/tests -q`).
> - Critério de aceite de cada item: RF/RN/RNF correspondente do documento de requisitos.

---

## Sprint 0 — Higiene e fundação ✅ (já feito)

Concluído antes desta divisão em sprints. Não refazer.

- Setup Docker Compose (backend + frontend com hot-reload, volumes nomeados).
- Backend mínimo: `/api/health`.
- Frontend mínimo: Vue 3 + Vite + Pinia + Vue Router com shell, sidebar e tela placeholder.
- `backend/cypher.db` via SQLite local + seed de categorias padrão.
- `README.md` e `AGENTS.md` atualizados; `project.md` como snapshot vivo.

---

## Sprint 1 — Core de transações e dashboard

**Objetivo:** fechar o loop básico de finanças pessoais. Após esta sprint, o usuário consegue cadastrar transações, ver saldo/dashboard e consultar histórico.

### Backend
- [ ] **RF-01** Cadastrar transação (`POST /api/transactions`) — já existe, validar robustez
- [ ] **RF-02** Listar transações com filtros (`GET /api/transactions`) — já existe
- [ ] **RF-03** Editar e excluir (`PUT/DELETE /api/transactions/{id}`) — já existe
- [ ] **RF-04** Dashboard: saldo, receitas, despesas do mês (`GET /api/dashboard`) — já existe
- [ ] **RN-01** Saldo calculado (nunca armazenado) — já garantido
- [ ] **RN-02** Categoria obrigatória + seed padrão — já existe
- [ ] **RN-03** Data não-futura — já existe (validador Pydantic)
- [ ] **RN-07** `type` validado como `income|expense` — já existe
- [ ] Testes pytest cobrindo CRUD + filtros + validações (RF-01..04)

### Frontend
- [ ] View `DashboardView` ligada a `/api/dashboard` — preencher cards (saldo, receitas, despesas, variação)
- [ ] View `TransactionsView` com formulário de cadastro (data, tipo, valor, categoria, descrição)
- [ ] Listagem de transações com filtros (período, categoria, tipo)
- [ ] Edição e exclusão inline ou via modal
- [ ] Store Pinia de transações (substituir `stores/counter.js`)
- [ ] Integração `services/api.js` com tratamento de erro amigável (RNF-07)

### Critério de aceite
Usuário abre o app, cadastra uma receita e uma despesa, vê o saldo atualizar no dashboard, filtra a lista por mês e edita um registro.

---

## Sprint 2 — Orçamento e categorias

**Objetivo:** controle de gastos por categoria com limites mensais e alertas visuais.

### Backend
- [ ] **RF-08** Definir limite mensal por categoria (`PUT /api/categories/{id}/budget`) — já existe
- [ ] **RF-08** Endpoint `/api/budgets` retornando `limit`, `spent`, `percent` — já existe
- [ ] **RN-04** Orçamento mensal (reset por mês) — já implícito nos cálculos
- [ ] Testes: budget de categoria com gasto abaixo, no limite e acima

### Frontend
- [ ] View `BudgetsView` listando categorias com barra de progresso (`barra_porcentagem.vue`)
- [ ] Edição inline do limite por categoria
- [ ] **RF-09** Alerta visual quando categoria atingir 80% (amarelo) e 100% (vermelho)
- [ ] Integração no `DashboardView`: card de orçamento destacado se alguma categoria estoura

### Critério de aceite
Usuário define R$ 800 para Alimentação, cadastra despesas que somam R$ 640, vê a barra em amarelo; ao passar de R$ 800, a barra fica vermelha com mensagem de alerta.

---

## Sprint 3 — Exportação e metas de poupança

**Objetivo:** entregáveis rápidos (CSV) e o módulo completo de metas.

### Backend
- [ ] **RF-07** Exportar CSV (`GET /api/transactions/export.csv`) reaproveitando filtros
- [ ] **RF-18, RF-19** CRUD de metas (`/api/goals`) — já existe, polir
- [ ] **RF-20, RF-23** Depósitos em metas (`/api/goals/{id}/deposits`) — já existe
- [ ] **RF-21** Progresso (`saved_amount`, `percent`, `is_completed`) — já existe
- [ ] **RF-22** Backend sinaliza `is_completed: true` quando `saved >= target` — já existe
- [ ] **RF-24** Editar/excluir meta (preservar depósitos via cascade) — já existe
- [ ] Testes: criação, depósito, conclusão automática, exclusão em cascata

### Frontend
- [ ] View `GoalsView` com lista de metas + barra de progresso
- [ ] Formulário de criar/editar meta (nome, valor, prazo, descrição)
- [ ] Tela de detalhe da meta com histórico de depósitos (`RF-23`)
- [ ] **RF-22** Toast/banner de parabéns ao concluir meta (no momento do depósito que atinge 100%)
- [ ] Botão "Exportar CSV" em `TransactionsView` consumindo o endpoint

### Critério de aceite
Usuário cria meta "Viagem" de R$ 5.000, lança depósitos mês a mês, vê o progresso, recebe notificação visual ao bater a meta e baixa um CSV das transações do mês corrente.

---

## Sprint 4 — Carteira de investimentos

**Objetivo:** cadastro de ativos, cotações reais e dashboard de investimentos.

### Backend
- [ ] **RF-10** Modelo `Investment` + CRUD `/api/investments`
  - Campos: `id, ticker, name, type, quantity, avg_price, purchase_date` (ver modelo no doc §5)
- [ ] **RF-11** Integração yfinance para cotações (`pip install yfinance`)
  - Endpoint `/api/investments/quotes?tickers=PETR4.SA,BTC-USD`
- [ ] **RNF-04** Cache de 1h no backend para cotações (em memória ou tabela `quote_cache`)
- [ ] **RNF-08** Fallback: retornar última cotação conhecida com `stale: true` se yfinance falhar
- [ ] **RF-12** Dashboard de investimentos:
  - Patrimônio total = Σ (qty × cotação atual)
  - Rentabilidade por ativo = `(cotação - avg_price) / avg_price`
  - Alocação por tipo (acao/fii/cripto/renda_fixa)
- [ ] **RN-05** Ticker BR com sufixo `.SA` documentado no helper de validação
- [ ] **RN-08** Quantidade e preço médio > 0 (Pydantic validators)
- [ ] Testes: cadastro, cálculo de rentabilidade, fallback de cotação, expiração de cache

### Frontend
- [ ] View `InvestmentsView` com lista de ativos + rentabilidade
- [ ] Formulário de cadastro de ativo com seletor de tipo
- [ ] Card de patrimônio total e gráfico de alocação (Chart.js donut)
- [ ] Indicador visual de cotação "desatualizada" quando `stale: true`

### Critério de aceite
Usuário cadastra 10 PETR4 a R$ 30, vê o preço atual via yfinance, calcula rentabilidade em tempo real e a alocação no donut chart.

---

## Sprint 5 — Simulações financeiras

**Objetivo:** projeções para planejamento (sem afetar saldo real).

### Backend
- [ ] **RF-14** Juros compostos: `POST /api/simulations/compound-interest`
- [ ] **RF-15** Aposentadoria: `POST /api/simulations/retirement`
- [ ] **RF-16** Meta financeira: `POST /api/simulations/goal`
- [ ] **RF-17** Monte Carlo: `POST /api/simulations/monte-carlo` (1000 cenários, percentis 10/50/90)
- [ ] Instalar Pandas + NumPy; criar `services/simulations.py` separado
- [ ] Modelo `Simulation` (id, name, type, params_json, result_json, created_at)
- [ ] Persistir simulação para o usuário revisitar
- [ ] **RN-06** Simulações não criam transações reais — garantir isolamento

### Frontend
- [ ] View `SimulationsView` com abas: juros compostos, aposentadoria, meta, Monte Carlo
- [ ] Formulários com inputs explicativos (capital inicial, aporte, taxa, prazo)
- [ ] Gráficos de projeção (Chart.js line) com série base e banda Monte Carlo (percentis)

### Critério de aceite
Usuário simula R$ 1.000/mês por 10 anos a 1% a.m. e vê a curva exponencial; roda Monte Carlo e observa a banda de cenários pessimista/realista/otimista.

---

## Sprint 6 — Transações recorrentes

**Objetivo:** gerenciar receitas e despesas que se repetem no tempo, sem criar transações automáticas.

### Backend
- [ ] Modelo `RecurringTransaction` (id, name, type, amount, category_id, frequency, interval, day_of_month, day_of_week, start_date, end_date, is_active, notify_before_days, notify_on_due, created_at)
- [ ] Modelo `RecurringOccurrence` (id, recurring_id, due_date, amount, status, transaction_id, confirmed_at, created_at)
- [ ] Endpoints CRUD `/api/recurring-transactions`
- [ ] **RF-26** `POST /api/recurring-transactions/{id}/generate-occurrences` calcula próximas ocorrências dentro de um horizonte (ex.: próximos 12 meses) sem criar transações
- [ ] **RF-27** `POST /api/occurrences/{id}/confirm` cria a transação real e marca ocorrência como `received|paid`
- [ ] **RF-30** `GET /api/occurrences?period=YYYY-MM&type=...&status=...` — agenda filtrada
- [ ] **RF-31** `GET /api/occurrences/summary?period=YYYY-MM` — resumo previsto vs realizado
- [ ] **RF-33** Histórico de ocorrências com filtros por status
- [ ] **RF-32** Pausar/reativar/excluir recorrência sem alterar ocorrências confirmadas
- [ ] **RN-09, RN-10** Ocorrência ≠ transação; previsto não altera saldo
- [ ] **RN-11** Histórico imutável (recorrência editada não mexe em ocorrências confirmadas)
- [ ] **RN-13** Próxima ocorrência calculada a partir da última válida
- [ ] Testes: geração de ocorrências com frequências (daily/weekly/monthly/yearly), confirmações, isolamento entre previsto e saldo real

### Frontend
- [ ] View `RecurringView` (lista de recorrências ativas/pausadas/encerradas)
- [ ] Formulário de criar/editar recorrência com seletor de frequência
- [ ] View `AgendaView` (calendário + lista de ocorrências próximas) com filtros
- [ ] Card de "próximos vencimentos" no dashboard
- [ ] Modal de confirmação de ocorrência: confirmar / adiar / ignorar / marcar como não recebida

### Critério de aceite
Usuário cadastra "Salário" mensal de R$ 5.000, gera ocorrências dos próximos 12 meses, visualiza na agenda, confirma uma ocorrência e vê a transação real criada e refletida no saldo.

---

## Sprint 7 — Sistema de notificações locais

**Objetivo:** alertas de vencimento e pendências sem dependência de serviços externos (RNF-10).

### Backend
- [ ] Modelo `Notification` (id, occurrence_id, type, scheduled_at, sent_at, status, created_at) — type ∈ `before_due|due|overdue`
- [ ] Scheduler no processo FastAPI (ex.: APScheduler) que varre ocorrências e gera notificações conforme configuração
- [ ] **RF-28** Notificar antes e no dia do vencimento (`notify_before_days`, `notify_on_due`)
- [ ] **RF-29** Marcar ocorrência como `overdue` após vencimento sem confirmação e reagendar alerta
- [ ] **RF-34** Endpoint `/api/notifications/preferences` para configurar antecedência, horário e tipos ativos
- [ ] **RNF-11** Persistência do agendamento (fila em SQLite + scheduler no startup)
- [ ] **RNF-12** Prevenção de duplicidade: uma vez `sent_at` preenchido, não reagendar
- [ ] **RN-12** Receita pendente continua `overdue` até resolução
- [ ] **RN-14** Cada alerta dispara no máximo uma vez por ocorrência e tipo
- [ ] Testes: agendamento não duplica, marcação de overdue, preferências aplicadas

### Frontend
- [ ] Tela de preferências de notificação (antecedência, horário silencioso, tipos)
- [ ] **RF-35** Notificação Web (Notification API do browser) com ação rápida "Confirmar recebimento"
- [ ] Sino de notificações no header com lista de pendentes

### Critério de aceite
Usuário recebe notificação 2 dias antes do vencimento da conta de luz, clica e é levado à ocorrência; se não confirmar até a data, recebe alerta de overdue no dia seguinte.

---

## Sprint 8 — Empacotamento desktop (Electron)

**Objetivo:** entregar o `.exe`/`.dmg`/`.AppImage` único com Python embarcado.

### Infraestrutura
- [ ] Criar `desktop/` com `package.json` próprio para Electron
- [ ] `electron/main.js`: cria `BrowserWindow`, gerencia subprocesso Python
- [ ] Empacotar `backend/` (código + `requirements.txt`) e Python runtime (via `pyinstaller` ou `python-build-standalone`)
- [ ] **RNF-09** Usuário final não precisa instalar Python/Node
- [ ] **RNF-05** Backend inicia em < 5s, com tela de loading no splash
- [ ] **RNF-06** Janela mínima 1024×640, responsivo até 4K
- [ ] Devolver `VITE_API_URL` apontando para `http://127.0.0.1:<porta-dinâmica>` injetada pelo Electron
- [ ] **RNF-03** Garantir que nenhum dado sai da máquina (fase 1); yfinance é a única exceção
- [ ] `electron-builder` configurado para Windows/Mac/Linux
- [ ] Ícone, instalador, README com screenshots
- [ ] Smoke test do `.exe` gerado em máquina limpa

### Critério de aceite
Usuário baixa `Cypher-Setup.exe`, instala, abre o app sem instalar Python/Node, vê o splash por < 5s e está na tela inicial com dados persistidos localmente.

---

## Backlog (pós-MVP, sprints futuras)

Itens já previstos no documento de requisitos, fora do escopo do MVP desktop:

| Ref | Item | Sprint sugerida |
|---|---|---|
| RF-13 | Comparar dois ativos (gráfico comparativo) | Sprint 5 ou 9 |
| RF-36..43 | Cartão de crédito (limites, faturas, parcelas) | Sprint 9 |
| RF-44..51 | Sincronização bancária (Open Finance) | Sprint 10 |
| RF-52..58 | App mobile (Vue 3 + Capacitor ou Native) | Sprint 11+ |
| RNF-13..17 | Autenticação, sync criptografado, segurança bancária | Sprint 10+ |

Cada um desses itens exige modelagem nova (tabelas `accounts`, `credit_cards`, `credit_card_purchases`, `credit_card_installments`, `credit_card_invoices`, `bank_connections`, `imported_transactions`, `sync_logs`) e UI dedicada — tratados em sprints próprias quando priorizados.

---

## Resumo visual

```
Sprint 0  ▰▰▰▰▰ Higiene + Docker       ✅ pronto
Sprint 1  ░░░░░ Transações + Dashboard → RF-01..04, RN-01..03, RN-07
Sprint 2  ░░░░░ Orçamento + Alertas    → RF-08, RF-09, RN-04
Sprint 3  ░░░░░ CSV + Metas             → RF-07, RF-18..24
Sprint 4  ░░░░░ Investimentos           → RF-10..12, RF-11, RN-05, RN-08, RNF-04, RNF-08
Sprint 5  ░░░░░ Simulações              → RF-14..17, RN-06
Sprint 6  ░░░░░ Recorrências            → RF-25..33, RN-09..13
Sprint 7  ░░░░░ Notificações            → RF-28..29, RF-34..35, RNF-10..12, RN-12, RN-14
Sprint 8  ░░░░░ Empacotamento Electron  → RNF-01, RNF-05, RNF-06, RNF-09, RNF-03
```

**Total:** 8 sprints para chegar ao MVP desktop distribuível. Cada sprint = 1 PR com backend + frontend + testes.
