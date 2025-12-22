# 🔧 Fix: Add 'role' Column to Database

## Error
```
psycopg2.errors.UndefinedColumn: column users.role does not exist
```

## Cause
The code has been updated to include `role` field, but the database table hasn't been migrated yet.

---

## ✅ Solution: Add Role Column

### **Method 1: Using Python Script (Easiest - Recommended)**

Make sure you're in the virtual environment, then run:

```bash
cd "insurance-ai-frontend/Innsurance Backend Fast API"

# Activate virtual environment (if using venv)
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Run migration script
python run_migration.py
```

**OR if you're already in the backend directory with venv activated:**

```bash
python run_migration.py
```

### **Method 2: Using SQL Directly (Azure Portal / psql)**

Connect to your PostgreSQL database and run:

```sql
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS role VARCHAR(20) DEFAULT 'user';

-- Update existing users
UPDATE users 
SET role = 'user' 
WHERE role IS NULL;
```

**How to connect:**
- **Azure Portal**: Go to your PostgreSQL server → Query Editor
- **psql command line**: 
  ```bash
  psql "postgresql://dbadmin:admin@123@insurance-ai-postgres-dev.postgres.database.azure.com:5432/postgres?sslmode=require"
  ```

### **Method 3: Using Swagger UI (Temporary Workaround)**

If you can't run SQL directly, you can temporarily modify the code to handle missing column gracefully, but this is NOT recommended for production.

---

## 🧪 Verify Column Was Added

After running the migration, verify:

```sql
SELECT column_name, data_type, column_default 
FROM information_schema.columns 
WHERE table_name = 'users' AND column_name = 'role';
```

Should return:
```
column_name | data_type | column_default
------------|-----------|---------------
role        | varchar   | 'user'
```

---

## 🚀 After Migration

1. Restart your backend server
2. Try login again
3. Create admin user using `POST /users/` with `"role": "admin"`

---

**Quick SQL Command:**
```sql
ALTER TABLE users ADD COLUMN IF NOT EXISTS role VARCHAR(20) DEFAULT 'user';
```

