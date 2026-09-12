# Cypher — MVP local

Aplicação de finanças pessoais local, com transações, dashboard, orçamentos e metas.

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
