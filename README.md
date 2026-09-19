# Cypher — MVP local

Aplicação local de finanças pessoais, com transações, dashboard, orçamentos, metas, recebimentos, recorrências, cartões e assinaturas SaaS.

## Assinaturas SaaS

Em **Assinaturas SaaS**, é possível cadastrar clientes, produtos, planos e contratos com ciclos mensal, trimestral, semestral ou anual. O sistema gera cobranças previstas sem duplicidade, aceita recebimentos parciais e cria uma receita no financeiro somente quando a baixa é confirmada. A reversão do recebimento também remove a receita vinculada.

## Executar em desenvolvimento

Em um terminal, inicie a API:

```powershell
cd backend
python -m pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8000
```

Em outro terminal, inicie a interface:

```powershell
cd frontend
pnpm install
pnpm dev
```

Abra a URL indicada pelo Vite (normalmente `http://localhost:5173`). O arquivo SQLite `backend/cypher.db` é criado automaticamente e permanece apenas no computador local.

## Verificar

```powershell
python -m pytest backend/tests -q
pnpm --dir frontend build
```

## Android independente

O app Android vive em `mobile/cypher-android` e não compartilha código ou dependências com o frontend desktop. Após instalar o Android Studio com o SDK Android, sincronize os assets e gere o APK de teste:

```powershell
cd mobile/cypher-android
pnpm install
pnpm android:sync
cd android
.\gradlew.bat assembleDebug
```

O APK de desenvolvimento fica em `mobile/cypher-android/android/app/build/outputs/apk/debug/app-debug.apk`. Ele é assinado automaticamente com a chave de debug e pode ser instalado diretamente em um aparelho Android. Para uma distribuição de produção, configure uma chave de assinatura própria antes de gerar `assembleRelease`.

## Edições modulares

As áreas do produto Android são declaradas em `mobile/cypher-android/src/modules/catalog.json`. Cada módulo registra sua rota, tela, item de navegação, descrição e dependências. As edições escolhem apenas os módulos de entrada em `mobile/cypher-android/editions/*.json`; dependências são incluídas automaticamente.

```powershell
pnpm --dir mobile/cypher-android build:complete
pnpm --dir mobile/cypher-android build:personal
pnpm --dir mobile/cypher-android build:essentials
pnpm --dir mobile/cypher-android build:saas
```

Para gerar os assets Android de uma edição, execute `pnpm --dir mobile/cypher-android android:personal`, `android:essentials` ou `android:saas`, depois rode `assembleDebug` dentro de `mobile/cypher-android/android`. A edição ativa só contém as rotas e telas declaradas no seu JSON.
