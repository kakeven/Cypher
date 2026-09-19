# Plano — Módulo de Assinaturas SaaS

## 1. Objetivo

Adicionar ao Cypher um módulo de receita recorrente para controlar os SaaS da Tervo: clientes, serviços contratados, mensalidades, vencimentos, pagamentos, inadimplência e receita mensal recorrente (MRR).

O módulo será separado das finanças pessoais, mas cada pagamento confirmado criará uma transação de receita no financeiro. Assim, a assinatura informa a previsão e o financeiro registra apenas o dinheiro efetivamente recebido.

## 2. Escopo do MVP

O MVP será manual: você registra ou confirma os pagamentos recebidos. Ele não fará cobranças automáticas, emissão de boleto, Pix, e-mail ou integração com gateway nesta etapa.

### Incluído

- Cadastro de clientes.
- Cadastro dos produtos/serviços SaaS da Tervo.
- Cadastro de planos reutilizáveis e assinaturas com preço customizável.
- Ciclos mensal, trimestral, semestral e anual.
- Geração idempotente das cobranças previstas.
- Confirmação de pagamento total ou parcial.
- Situações: ativa, pausada, atrasada, cancelada e encerrada.
- Próximos vencimentos, atrasos e histórico.
- Indicadores: MRR contratado, previsto, recebido, em atraso, clientes ativos e cancelamentos.
- Criação automática de uma `Transaction` de receita ao receber o pagamento.

### Fora do MVP

- Mercado Pago, Asaas, Stripe, Open Finance ou webhook.
- Cobrança automática, boleto, Pix dinâmico ou nota fiscal.
- Envio de WhatsApp/e-mail.
- Multiusuário, sincronização cloud e aplicativo mobile.
- Cálculo sofisticado de churn/cohortes; manter somente métricas simples no começo.

## 3. Decisões de domínio

1. Assinatura não é receita: ela representa um contrato e sua expectativa de cobrança.
2. Cobrança não é pagamento: uma cobrança vence em uma data; só ao registrar um pagamento ela produz receita no financeiro.
3. Uma cobrança pode ter mais de um pagamento. Isso cobre parcial, entrada e complemento sem gambiarra.
4. O valor, produto e plano da assinatura devem ser copiados para a cobrança quando ela é criada. Alterar a assinatura não pode reescrever o histórico.
5. Cancelar uma assinatura não exclui cobranças nem transações anteriores. Deve interromper somente novas cobranças após a data de término.
6. O `transaction_id` no pagamento garante o vínculo e impede criar duas receitas para a mesma baixa.
7. O MVP terá um único contexto empresarial: Tervo. Não criar multi-tenant nem tabela de empresas agora.

## 4. Modelo de dados

### `saas_clients`

| Campo | Regra |
|---|---|
| id | PK |
| name | obrigatório |
| business_name | opcional |
| contact_name | opcional |
| whatsapp | opcional |
| email | opcional |
| notes | opcional |
| is_active | padrão `true` |
| created_at | obrigatório |

### `saas_products`

Representa o que a Tervo vende, por exemplo: Catálogo de Celulares, Gestão de Loja ou Agenda de Arenas.

| Campo | Regra |
|---|---|
| id | PK |
| name | único, obrigatório |
| description | opcional |
| is_active | padrão `true` |
| created_at | obrigatório |

### `saas_plans`

É opcional na criação de uma assinatura, porque contratos sob medida não devem ser forçados a caber em um plano.

| Campo | Regra |
|---|---|
| id | PK |
| product_id | FK para `saas_products` |
| name | obrigatório por produto |
| default_amount | positivo |
| billing_cycle | `monthly`, `quarterly`, `semiannual` ou `yearly` |
| is_active | padrão `true` |

### `saas_subscriptions`

| Campo | Regra |
|---|---|
| id | PK |
| client_id | FK para cliente |
| product_id | FK para produto |
| plan_id | FK opcional para plano |
| name | nome exibido do contrato |
| amount | valor contratado, positivo |
| billing_cycle | ciclo copiado ou definido no contrato |
| due_day | 1 a 28 para contratos mensais; evita problemas de fevereiro |
| start_date | obrigatório |
| end_date | opcional |
| status | `active`, `paused`, `canceled` ou `ended` |
| canceled_at | opcional |
| notes | opcional |
| created_at | obrigatório |

### `saas_invoices`

Mesmo sem emitir nota fiscal, o nome `invoice` representa uma cobrança prevista.

| Campo | Regra |
|---|---|
| id | PK |
| subscription_id | FK para assinatura |
| reference_period | `YYYY-MM` ou período equivalente |
| due_date | obrigatório |
| amount | snapshot do valor cobrado |
| status | `pending`, `partial`, `paid`, `overdue`, `void` |
| created_at | obrigatório |

Índice único: `(subscription_id, reference_period)`. Ele é a proteção principal contra cobranças duplicadas.

### `saas_payments`

| Campo | Regra |
|---|---|
| id | PK |
| invoice_id | FK para cobrança |
| amount | positivo e não pode ultrapassar o saldo pendente |
| paid_at | data efetiva do recebimento |
| payment_method | `pix`, `cash`, `card`, `transfer`, `other` |
| transaction_id | FK única para `transactions` |
| note | opcional |
| created_at | obrigatório |

## 5. Regras de negócio

- Uma assinatura ativa gera somente uma cobrança por período.
- Assinatura pausada, cancelada ou encerrada não gera novas cobranças.
- Ao abrir o módulo ou dashboard, gerar cobranças até 90 dias à frente; disponibilizar uma ação explícita para gerar 12 meses quando necessário.
- Uma cobrança vencida sem quitação total passa para `overdue`; pagamento parcial permanece `partial`.
- Ao registrar uma baixa, criar uma transação `income` com a data e o valor pagos. A descrição deve identificar cliente, produto e período.
- A transação vinculada usa uma categoria específica `Assinaturas SaaS`, criada automaticamente se ainda não existir. Isso evita misturar a receita recorrente da Tervo com receitas pessoais genéricas.
- Desfazer uma baixa deve remover ou estornar a transação vinculada e recalcular a situação da cobrança. Exigir confirmação na interface.
- O MRR considera somente assinaturas ativas normalizadas para mês: mensal = valor; trimestral = valor/3; semestral = valor/6; anual = valor/12.
- Receita recebida considera `saas_payments.paid_at`, não a data de vencimento.

## 6. API e arquitetura backend

Manter o padrão atual `router → service → repository` em `backend/app/subscriptions/`.

### Endpoints

| Método | Rota | Responsabilidade |
|---|---|---|
| GET/POST | `/api/saas-clients` | listar e criar clientes |
| PUT | `/api/saas-clients/{id}` | editar cliente |
| GET/POST | `/api/saas-products` | listar e criar produtos |
| PUT | `/api/saas-products/{id}` | editar/arquivar produto |
| GET/POST | `/api/saas-plans` | listar e criar planos |
| PUT | `/api/saas-plans/{id}` | editar/arquivar plano |
| GET/POST | `/api/saas-subscriptions` | listar e criar contratos |
| GET/PUT | `/api/saas-subscriptions/{id}` | detalhe e edição |
| POST | `/api/saas-subscriptions/{id}/pause` | pausar |
| POST | `/api/saas-subscriptions/{id}/resume` | reativar |
| POST | `/api/saas-subscriptions/{id}/cancel` | cancelar com data |
| POST | `/api/saas-subscriptions/generate-invoices` | gerar cobranças, com período final opcional |
| GET | `/api/saas-invoices` | filtro por status, cliente, vencimento e período |
| POST | `/api/saas-invoices/{id}/payments` | registrar recebimento e criar receita |
| DELETE | `/api/saas-payments/{id}` | estornar baixa, com confirmação no front |
| GET | `/api/saas-dashboard` | MRR, recebido, previsto, atraso e renovação |

### Organização sugerida

```text
backend/app/subscriptions/
├── model.py
├── schema.py
├── repository.py
├── service.py
├── router.py
└── invoice_generation.py
```

`invoice_generation.py` concentra a lógica de datas e períodos. Ela deve ter testes unitários próprios, pois datas recorrentes são onde os pequenos demônios financeiros moram.

## 7. Interface

Adicionar à sidebar um item `Assinaturas SaaS`. A tela será desktop-first, consistente com o limite atual de 1024px.

### Visão geral

- Cards: MRR, recebido no mês, previsto no mês, em atraso e assinaturas ativas.
- Lista de próximos vencimentos com ações rápidas: `Registrar pagamento` e `Ver cliente`.
- Lista de atrasados destacada, mas sem usar vermelho em tudo; vermelho só onde exige ação.

### Telas

1. **Assinaturas** — tabela com cliente, produto, valor, próximo vencimento, status e menu de ações.
2. **Cobranças** — filtros de período/status, saldo pendente, baixa parcial e histórico de pagamentos.
3. **Clientes** — cadastro simples e visão de todas as assinaturas daquele cliente.
4. **Produtos e planos** — administração de ofertas reutilizáveis.
5. **Detalhe da assinatura** — linha do tempo de cobranças e pagamentos, edição, pausa e cancelamento.

Usar uma store Pinia `subscriptions` e ampliar `src/services/api.js`; não criar chamadas HTTP diretamente nas views.

## 8. Integração com financeiro atual

1. O serviço de pagamento começa uma transação no banco.
2. Valida que a cobrança existe e que o saldo comporta a baixa.
3. Cria `Transaction(type='income')` na categoria `Assinaturas SaaS`.
4. Cria `SaasPayment` com o `transaction_id` retornado.
5. Atualiza o status da cobrança para parcial ou paga.
6. Confirma a transação atômica.

Se qualquer passo falhar, nenhum registro deve permanecer. Isso protege especialmente contra a duplicidade que faria o dashboard parecer mais rico que a Tervo de verdade.

## 9. Plano de execução

### Sprint 1 — Domínio e segurança dos dados

- Criar os modelos, schemas e repositórios.
- Registrar modelos no startup do SQLAlchemy.
- Criar a categoria interna `Assinaturas SaaS` de forma idempotente.
- Implementar clientes, produtos, planos e CRUD de assinaturas.
- Escrever testes para validações, ciclos e transições de status.

**Entrega:** contratos SaaS podem ser cadastrados e gerenciados, sem pagamentos ainda.

### Sprint 2 — Cobranças e integração financeira

- Implementar geração idempotente de cobranças.
- Implementar lista, filtros e cálculo de atraso.
- Registrar pagamento total/parcial e a transação de receita atômica.
- Implementar estorno protegido de pagamento.
- Testar duplicidade, parcial, cancelamento e datas de virada de mês.

**Entrega:** o Cypher controla previsão, recebimento e inadimplência sem duplicar receitas.

### Sprint 3 — Interface e indicadores

- Criar rotas, store e telas de Assinaturas, Cobranças, Clientes e Produtos/Planos.
- Implementar formulários, menus de pausa/cancelamento e confirmação de ações irreversíveis.
- Integrar dashboard SaaS e cards principais.
- Validar build do frontend e fluxo completo pelo navegador.

**Entrega:** módulo utilizável no dia a dia da Tervo.

### Sprint 4 — Qualidade e documentação

- Cobrir os cenários de negócio críticos com `pytest`.
- Adicionar testes de componente ou E2E para fluxo de receber mensalidade.
- Atualizar `project.md`, `README.md` e `sprints.md`.
- Rodar `docker compose build`, testes backend e build frontend.

**Entrega:** módulo documentado e verificável antes de novas integrações.

## 10. Critérios de aceite

- Consigo cadastrar a assinatura de um cliente com valor mensal e data de vencimento.
- O sistema mostra a mensalidade como prevista, sem alterar o saldo real.
- Ao registrar R$ 99 recebidos, aparece uma receita de R$ 99 uma única vez no financeiro.
- Se o cliente pagar R$ 50 de R$ 99, a cobrança fica parcial e o financeiro recebe apenas R$ 50.
- Não consigo gerar duas cobranças do mesmo contrato para o mesmo período.
- Cancelar uma assinatura mantém o histórico e não cria novos vencimentos.
- O dashboard informa com clareza quanto entra por mês, quanto foi recebido e o que está atrasado.

## 11. Evolução posterior

Depois do MVP estar estável, a próxima evolução recomendada é integração com Asaas ou Mercado Pago por webhook. O webhook deve ser idempotente e armazenar um identificador externo único por pagamento antes de criar qualquer receita. Só então faz sentido automatizar lembretes de WhatsApp e cobrança.
