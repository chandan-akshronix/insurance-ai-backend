# 🚨 QUICK FIX: Add Role Column

## The Error
```
psycopg2.errors.UndefinedColumn: column users.role does not exist
```

## ⚡ FASTEST SOLUTION

### **Option 1: Run Python Script (30 seconds)**

Open a **NEW terminal** in the backend directory and run:

```bash
cd "insurance-ai-frontend/Innsurance Backend Fast API"
venv\Scripts\activate
python run_migration.py
```

### **Option 2: Run SQL Directly (1 minute)**

1. Go to **Azure Portal** → Your PostgreSQL Server
2. Click **"Query Editor"** (or use any PostgreSQL client)
3. Run this SQL:

```sql
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS role VARCHAR(20) DEFAULT 'user';

UPDATE users 
SET role = 'user' 
WHERE role IS NULL;
```

4. Click **"Run"**

### **Option 3: Using psql Command Line**

```bash
psql "postgresql://dbadmin:admin@123@insurance-ai-postgres-dev.postgres.database.azure.com:5432/postgres?sslmode=require"

# Then run:
ALTER TABLE users ADD COLUMN IF NOT EXISTS role VARCHAR(20) DEFAULT 'user';
\q
```

---

## ✅ After Running Migration

1. **Restart your backend server** (stop uvicorn and start again)
2. **Try login again** - the error should be gone!

---

## 🎯 One-Line SQL Command

```sql
ALTER TABLE users ADD COLUMN IF NOT EXISTS role VARCHAR(20) DEFAULT 'user';
```

Copy-paste this into Azure Portal Query Editor and click Run!

