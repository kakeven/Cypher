# Cypher — estado atual do projeto

> Snapshot verificado em 12/09/2026 a partir do código-fonte, configuração e testes presentes no repositório. Atualize este arquivo após mudanças significativas de escopo, arquitetura, modelos ou endpoints.

## Visão geral

Cypher é um MVP local de finanças pessoais. No estado atual, ele roda como dois processos de desenvolvimento: uma SPA Vue 3/Vite em `localhost:5173` e uma API FastAPI em `localhost:8000`. Os dados persistem em SQLite; o frontend consome a API por HTTP.

O produto já cobre transações, categorias e orçamento mensal, painel consolidado, metas com depósitos, recebíveis com baixas parciais, recorrências com agenda de ocorrências previstas e cartões de crédito com importação CSV Nubank. Ainda não há aplicação Electron, instalador ou subprocesso Python embarcado.

## Stack e execução

| Camada | Implementação atual |
|---|---|
| Frontend | Vue 3.5, Vite 8, Vue Router 5 e Pinia 3 |
| Backend | Python, FastAPI, Uvicorn, SQLAlchemy 2 e Pydantic v2 |
| Banco | SQLite; URL configurada por `CYPHER_DATABASE_URL` |
| Testes | pytest + FastAPI TestClient/httpx (backend); 27 testes passam no container em 13/09/2026 |
| Ambiente de desenvolvimento | Docker Compose com hot reload do Uvicorn e Vite HMR |

```powershell
# Ambiente completo
docker compose up --build

# Verificações
python -m pytest backend/tests -q
pnpm --dir frontend build
pnpm --dir frontend lint
```

Sem Docker, execute `python -m uvicorn main:app --reload --port 8000` em `backend/` e `pnpm dev` em `frontend/`. O frontend usa `VITE_API_URL` quando configurada; sem ela, usa `http://127.0.0.1:8000/api`.

## Estrutura relevante

```
Cypher/
├── backend/
│   ├── main.py                    # entrada FastAPI
│   ├── app/
│   │   ├── core/                  # base ORM, sessão, erros e valores monetários
│   │   ├── categories/            # categoria: model, schema, repository, service, router
│   │   ├── cards/                 # cartão, fatura e compras importadas: model, schema, repository, service, router
│   │   ├── transactions/          # transação: model, schema, repository, service, router
│   │   ├── dashboard/             # consultas consolidadas
│   │   ├── goals/                 # meta e depósito: model, schema, repository, service, router
│   │   ├── receivables/           # recebível e baixa: model, schema, repository, service, router
│   │   ├── recurring/              # recorrência e ocorrência: model, schema, repository, service, router
│   │   └── factory.py             # composição e startup da aplicação
│   ├── tests/test_api.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/            # shell, toast e campo de data
│   │   ├── composables/useToast.js
│   │   ├── router/index.js
│   │   ├── services/api.js
│   │   ├── stores/transactions.js
│   │   ├── utils/format.js
│   │   └── views/                 # dashboard, transações, orçamentos, metas e recebimentos
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
├── cypher-requisitos-v11-realocado.docx  # fonte de requisitos; não editar
├── sprints.md                             # planejamento, não snapshot de entrega
├── design-qa.md                           # QA visual pendente/bloqueado
├── README.md
└── project.md
```

## O que está implementado

### Backend e dados

- Arquitetura em camadas por domínio: `router → service → repository → SQLAlchemy`.
- Criação automática de tabelas no startup com `Base.metadata.create_all(engine)`; não há migrations formais.
- Seed, somente se o banco ainda não tiver categorias, de: Moradia, Alimentação, Transporte, Lazer, Saúde, Educação e Outros.
- Modelos persistidos:
  - `Category(id, name, color, budget_limit)`;
  - `Transaction(id, date, type, amount, category_id, description, created_at)`;
  - `Goal(id, name, target_amount, deadline, description, created_at)` e `GoalDeposit`;
- `Receivable(id, name, client, total_amount, service_type, category_id, created_at)` e `ReceivablePayment`.
- `CreditCard(id, name, brand, credit_limit, closing_day, due_day)`, `CreditCardInvoice`, `CreditCardPurchase` e `CreditCardInvoicePayment`.
- Compatibilidade pontual no startup: adiciona `service_type` à tabela antiga `receivables` quando a coluna não existe.
- Valores são armazenados como `Decimal`/`Numeric(12,2)` e serializados como número JSON.
- CORS restrito a `http://localhost:5173` e `http://127.0.0.1:5173`.

Regras de negócio efetivamente aplicadas:

- transações e baixas não aceitam data futura;
- transações aceitam apenas `income` ou `expense` e valor positivo; categoria é obrigatória somente para despesas e receitas são vinculadas internamente a `Outros`;
- saldo disponível é calculado a partir das transações, descontando depósitos de metas, e nunca persistido;
- nomes de categoria são únicos sem diferenciar maiúsculas/minúsculas;
- depósitos de meta compõem o progresso e marcam `is_completed` ao atingir a meta;
- cada baixa de recebível cria uma transação de receita vinculada, na categoria interna `Outros`; a baixa não pode ultrapassar o valor pendente;
- tipos de serviço de recebível são limitados a Site institucional, Sistema, E-commerce e Landing page.
- importação Nubank aceita CSV com `date`, `title` e `amount`, ignora lançamentos de `Pagamento recebido`, normaliza estornos, reconhece parcelas e bloqueia compras já importadas pelo identificador derivado do lançamento;
- pagamentos de fatura podem ser integrais ou parciais e identificam quem pagou; somente a parte paga pelo titular cria despesa no saldo. Pagamentos de terceiros reduzem exclusivamente o saldo pendente da fatura;
- compras de cartão permanecem nos relatórios da fatura e os pagamentos feitos pelo titular são excluídos desses relatórios para evitar dupla contagem.

### Endpoints expostos

Todos usam o prefixo `/api`.

| Método | Rota | Descrição |
|---|---|---|
| GET | `/health` | Verifica a disponibilidade da API e retorna `{"status":"ok"}` |
| GET | `/categories` | Lista categorias |
| POST | `/categories` | Cria categoria |
| PUT | `/categories/{id}` | Altera nome e cor da categoria |
| PUT | `/categories/{id}/budget` | Define ou limpa o limite mensal |
| DELETE | `/categories/{id}` | Exclui categoria sem uso ou a arquiva quando há histórico |
| GET | `/transactions` | Lista transações; filtros opcionais `date_from`, `date_to`, `category_id` e `type` |
| POST | `/transactions` | Cria transação |
| PUT | `/transactions/{id}` | Atualiza transação |
| DELETE | `/transactions/{id}` | Exclui transação (`204`) |
| GET | `/dashboard` | Saldo global, receitas/despesas e gastos por categoria do período; `period=YYYY-MM` opcional |
| GET | `/budgets` | Limite, gasto e percentual por categoria no período; `period=YYYY-MM` opcional |
| GET | `/goals` | Lista metas com progresso |
| POST | `/goals` | Cria meta |
| GET | `/goals/{id}` | Detalha uma meta, inclusive depósitos |
| PUT | `/goals/{id}` | Atualiza meta |
| DELETE | `/goals/{id}` | Exclui meta e depósitos (`204`) |
| POST | `/goals/{id}/deposits` | Registra depósito de meta |
| GET | `/receivables` | Lista recebíveis com totais e progresso |
| POST | `/receivables` | Cria recebível |
| GET | `/receivables/{id}` | Detalha recebível e baixas |
| PUT | `/receivables/{id}` | Atualiza recebível |
| DELETE | `/receivables/{id}` | Exclui recebível, baixas e receitas vinculadas (`204`) |
| POST | `/receivables/{id}/payments` | Registra baixa parcial e cria receita vinculada |
| GET/POST | `/recurring-transactions` | Lista ou cria recorrências |
| PUT/DELETE | `/recurring-transactions/{id}` | Atualiza ou exclui recorrência |
| POST | `/recurring-transactions/{id}/pause`, `/resume` | Pausa ou reativa uma recorrência |
| POST | `/recurring-transactions/{id}/generate-occurrences` | Gera ocorrências previstas, por padrão para 12 meses |
| GET | `/occurrences` | Lista ocorrências por período, tipo e status |
| GET | `/occurrences/summary` | Resume previsto e realizado no período |
| POST | `/occurrences/{id}/confirm` | Cria a transação real e confirma a ocorrência |
| GET/POST | `/credit-cards` | Lista ou cadastra cartões |
| GET | `/credit-cards/{id}` | Detalha cartão e faturas |
| POST | `/credit-cards/{id}/import-csv` | Importa CSV Nubank para a fatura selecionada |
| GET | `/credit-cards/invoices/{id}` | Detalha fatura e compras |
| DELETE | `/credit-cards/invoices/{id}` | Exclui uma fatura aberta e suas compras importadas |
| POST | `/credit-cards/invoices/{id}/payments` | Registra pagamento parcial, com pagador e efeito correto no saldo |
| PUT | `/credit-cards/purchases/{id}/category` | Define a categoria de uma compra |
| POST | `/credit-cards/invoices/{id}/pay` | Quita o restante da fatura, identificando quem realizou o pagamento |

Erros de domínio retornam `detail` em português com os códigos adequados, como `404`, `409` e `422`. Validações de contrato do Pydantic também retornam `422`.

### Frontend

- Shell de desktop com sidebar fixa, título dinâmico por rota e toaster global.
- Rotas ativas: `/dashboard`, `/transacoes`, `/orcamentos`, `/metas` e `/recebimentos`; `/` e rotas desconhecidas redirecionam para `/dashboard`.
- Dashboard consome os agregados da API e exibe o fluxo mensal de receitas e despesas em linhas separadas, além de uma rosquinha interativa de gastos por categoria, com legenda percentual, valores e atalho para o histórico filtrado. O card de despesas abate a parte da fatura que foi paga por terceiros.
- Transações têm formulário, filtros, edição e exclusão pelo menu de contexto com confirmação, além de store Pinia dedicado (`transactions`); receitas não pedem categoria na interface.
- Orçamentos permitem definir limites, editar nome/cor, resetar o orçamento ou excluir uma categoria pelo menu de contexto; categorias com histórico são arquivadas e preservam lançamentos antigos.
- Metas carregam os registros existentes ao abrir a tela e permitem criar, editar e excluir pelo menu de contexto com confirmação, selecionar o detalhe e incluir depósitos.
- Recebimentos permitem criar, editar e excluir projeto/serviço pelo menu de contexto com confirmação, acompanhar o saldo pendente e registrar baixas parciais.
- Agenda e recorrências permitem cadastrar receitas/despesas diárias, semanais, mensais ou anuais, gerar ocorrências previstas, pausar/reativar e editar/excluir pelo menu de contexto com confirmação. A confirmação cria a transação real; o previsto não altera o saldo.
- Cartões permitem cadastrar dados do cartão, importar o CSV Nubank localmente, conferir compras/estornos/parcelas, categorizar compras, excluir faturas abertas e registrar pagamento total ou parcial. Em ambos os modos, o usuário define se pagou ou se foi outra pessoa; apenas o próprio pagamento reduz o saldo. Compras categorizadas entram no orçamento e no ranking de gastos no mês de referência da fatura; o pagamento não é contado novamente nesses relatórios.
- Cliente HTTP centralizado em `src/services/api.js`, incluindo normalização de mensagens de erro em português.
- Tema escuro com tokens CSS em `src/assets/variaveis.css`; a aplicação impõe largura mínima de 1024px, portanto não é responsiva para mobile.

### Infraestrutura e qualidade

- `docker-compose.yml` expõe backend em `8000` e frontend em `5173`.
- O Compose monta os fontes, persiste SQLite no volume `sqlite-data` e usa `frontend-node-modules` para dependências do frontend no container.
- Há testes de API para categorias, transações, filtros, dashboard, orçamento, metas, recebíveis e validações relevantes em `backend/tests/test_api.py`.
- Não há testes automatizados do frontend nem pipeline de CI configurado no repositório.
- Em 12/09/2026, `docker compose build`, `docker compose run --rm backend python -m pytest tests -q` e `docker compose run --rm frontend pnpm build` concluíram com sucesso. Com os serviços ativos, `GET /api/health` e `GET /dashboard` retornaram `200`.

## O que não está implementado

Prioridades e escopo devem ser confirmados contra o documento de requisitos e `sprints.md`; os itens abaixo não possuem implementação atual no código.

| Área | Gap atual |
|---|---|
| Exportação | Exportação CSV de transações não existe |
| Alertas de orçamento | Não há regra/interface específica para aviso de 80% ou estouro de limite |
| Investimentos | Sem modelos, endpoints, telas, gráficos, `yfinance` ou cache de cotações |
| Simulações | Sem cálculos de juros, aposentadoria, metas ou Monte Carlo |
| Cartão de crédito | Não há edição/exclusão de cartão, fatura automática por fechamento, limites disponíveis, parcelamento consolidado ou integração com outros bancos; a importação CSV Nubank está implementada |
| Notificações | Sem scheduler, preferências ou notificações locais/web |
| Cartão, sync bancário e mobile | Fora da implementação atual |
| Desktop distribuível | Sem diretório Electron, `electron-builder`, runtime Python empacotado ou instaladores |
| Visualização | Chart.js e Plotly não são dependências instaladas; dashboard não traz gráficos dessas bibliotecas |
| Responsividade e acessibilidade | Não há versão mobile e não há uma auditoria de acessibilidade concluída |
| Verificação visual | `design-qa.md` registra que a comparação com o protótipo foi bloqueada pela abertura local no navegador |

## Decisões e convenções registradas

1. O repositório é hoje uma aplicação web local de desenvolvimento, embora o objetivo de produto seja um desktop distribuível. A decisão de implementação futura é Electron; Tauri não está implementado.
2. SQLite é a fonte de dados local. `CYPHER_DATABASE_URL` é a única configuração de conexão: por padrão aponta para `backend/cypher.db` e, no Docker, para `/app/data/cypher.db`.
3. Novos domínios do backend devem preservar a separação router/service/repository e registrar os modelos antes do startup para que `create_all` os encontre.
4. Mensagens apresentadas pela API e pelo cliente permanecem em português.
5. Datas usam ISO `YYYY-MM-DD`; consultas e depósitos por mês usam `YYYY-MM`.
6. Arquivos Vue usam PascalCase para componentes e views atuais; não reintroduzir os antigos componentes em `snake_case` removidos do diretório.
7. O fluxo comercial de recebíveis não pede categoria financeira ao usuário; o backend vincula a receita criada à categoria `Outros`.
8. Não adicionar dependências sem justificativa; o projeto usa pnpm no frontend e os requisitos Python declarados em `backend/requirements.txt`. A importação CSV do Nubank usa apenas a biblioteca padrão do Python.
9. O host atual não tem `python` disponível no `PATH` e o `pnpm` local encontra `EPERM` em `frontend/node_modules`; use Docker Compose como ambiente de validação até que essas permissões/runtimes locais sejam corrigidos. O script `pnpm lint` também aplica `--fix`, portanto não deve ser usado como verificação puramente read-only.

## Observações para a próxima mudança

- O `project.md` anterior continha afirmações que não correspondiam à árvore atual, especialmente componentes antigos e um store `counter`; não use versões anteriores deste arquivo como referência de implementação.
- Há alterações não commitadas no repositório no momento deste snapshot. Este documento descreve os arquivos presentes no diretório de trabalho, não um commit Git específico.
